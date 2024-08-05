import streamlit as st
from ai71 import AI71
import chardet
import fitz
import langid
import pycountry
import re
import asyncio
import time
from docx import Document
import markdown2

# Access the API key from Streamlit secrets
ai71_api_key = st.secrets["AI71_API_KEY"]

# Initialize the AI71 client with the API key
client = AI71(api_key=ai71_api_key)

# Set page config with title and favicon
st.set_page_config(
    page_title="docXmart📃",
    page_icon="📃",
)

# Add custom CSS for styling
st.markdown(
    """
    <style>
    .main {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .sidebar .sidebar-content {
        background-color: #1034A6;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #2454FF;
        border-radius: 10px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #002FA7;
        color: #ffffff;
    }
    .stChatMessage--assistant {
        background-color: #e0e0e0;
        border-radius: 10px;
        padding: 10px;
    }
    .stChatMessage--user {
        background-color: #e0e0e0;
        border-radius: 10px;
        padding: 10px;
    }
    .title {
        color: #1034A6;
        font-size: 2em;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.write("""
**docXmart📃** is your intelligent multilingual assistant for all document-related tasks.
""")

st.sidebar.header("How to Use docXmart📃")
st.sidebar.write("""
1. **Upload Your Document**:
   - Provide a document in .txt, .md, .pdf, or .docx format.

2. **Describe Your Request**:
   - Choose a task from the prompt list (e.g., summarize, extract information, translate).

3. **Submit Your Request**:
   - Click 'Submit' to process your document.

4. **Review the Response**:
   - docXmart will analyze your document and generate a detailed response based on your instructions.
""")

st.sidebar.markdown("### Social Links:")
st.sidebar.write("🔗 [GitHub](https://www.github.com)")

# Show title and description.
st.markdown('<h1 class="title">docXmart 📃</h1>', unsafe_allow_html=True)
st.write(
    "This is docXmart, your multilingual assistant that helps with summarizing documents, highlighting important points, translating languages, and more."
)

# Function to get full language name
def get_full_language_name(lang_code):
    try:
        return pycountry.languages.get(alpha_2=lang_code).name
    except AttributeError:
        return lang_code

# Function to split document into chunks
def split_document(text, max_length=3000):
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index])
        text = text[split_index:]
    chunks.append(text)
    return chunks

# Create a session state variable to store the chat messages and document info
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.document = ""
    st.session_state.detected_language = None
    st.session_state.document_chunks = []
    st.session_state.current_chunk = 0

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Let the user upload a file via `st.file_uploader`.
uploaded_file = st.file_uploader(
    "Upload a document (.txt , .md , .docx or .pdf)", type=("txt", "md", "pdf", "docx")
)

async def generate_response(prompt_texts):
    full_response = ""
    response_placeholder = st.empty()
    for i, prompt_text in enumerate(prompt_texts):
        messages = [{"role": "user", "content": prompt_text}]
        try:
            response = await asyncio.to_thread(client.chat.completions.create,
                                               model="tiiuae/falcon-180b-chat",
                                               messages=messages)
            if response.choices and response.choices[0].message:
                chunk_response = response.choices[0].message.content
                chunk_response = re.sub(r'\s*user:\s*$', '', chunk_response, flags=re.IGNORECASE)
                full_response += chunk_response + " "
                response_placeholder.markdown(full_response)
                time.sleep(1)  # Simulate a delay for streaming effect
        except Exception as e:
            st.error(f"An error occurred while generating the response for chunk {i+1}: {e}")
            st.error(f"Details: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})

def read_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def read_md(file):
    content = file.read().decode("utf-8")
    html_content = markdown2.markdown(content)
    text_content = re.sub(r'<[^>]+>', '', html_content)
    return text_content

if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                st.session_state.document = " ".join([page.get_text() for page in doc])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            st.session_state.document = read_docx(uploaded_file)
        elif uploaded_file.type == "text/markdown":
            st.session_state.document = read_md(uploaded_file)
        else:
            raw_data = uploaded_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            st.session_state.document = raw_data.decode(encoding)

        # Detect language using langid
        detected_lang_code, _ = langid.classify(st.session_state.document)
        st.session_state.detected_language = get_full_language_name(detected_lang_code)

        st.success("Document uploaded and processed successfully!")
        # Display detected language with a color indicator
        if st.session_state.detected_language:
            color = "#" + "".join([hex(ord(c))[2:] for c in st.session_state.detected_language])[:6]
            st.markdown(f"""
                <div class="language-indicator" style="background-color: {color}; color: white;">
                    Detected Language: {st.session_state.detected_language}
                </div>
            """, unsafe_allow_html=True)

        # Creating categorized dropdown list for action selection
        general_prompts = [
            'Translate the document to another language',
            'Review and correct grammatical errors in the document',
            'Generate a concise summary of the document',
            'Extract specific information such as dates, names, and places from the document',
            'Determine the sentiment (positive, negative, neutral) expressed in the document',
            'Create new text based on the document’s content',
            'Expand on ideas or topics mentioned in the document',
            'Identify the main theme or subject of the document',
            'Rewrite sections of text to improve clarity or readability',
            'Identify and classify entities such as people, organizations, locations, and dates in the document',
            'Suggest improvements for style and readability of the document',
            'Identify and list important keywords or phrases from the document',
            'Analyze and identify recurring themes or topics within the document'
        ]
        educational_prompts = [
            'Generate text for PowerPoint slides based on the document',
            'Generate study notes based on the document',
            'Summarize educational content for easier understanding',
            'Create quiz questions based on the educational document',
            'Develop lesson plans or teaching materials from the document',
            'Provide examples and analogies to explain difficult concepts',
            'Identify and suggest additional resources for further reading',
            'Generate discussion questions to encourage critical thinking',
            'Analyze the document for educational standards alignment',
            'Suggest some possible visual aids that could be created based on the document',
            'Assess the readability level of the educational content'
        ]
        legal_prompts = [
        'Summarize legal documents and extract key points',
        'Translate legal documents to another language',
        'Identify key legal terms and definitions within the document',
        'Check for compliance with legal standards and regulations',
        'Draft legal contracts or agreements based on provided information',
        'Analyze and identify potential legal risks or issues',
        'Provide legal citations and references for document content',
        'Review and correct legal document formatting and structure',
        'Generate a timeline of events based on the legal document',
        'Assess the strength of arguments in legal documents'
        ]
        professional_prompts = [
        'Review and improve a resume',
        'Summarize a CV',
        'Extract key skills and qualifications from a resume',
        'Generate a professional summary based on a resume',
        'Tailor a resume for a specific job',
        'Identify strengths and weaknesses in a resume',
        'Convert a resume to a different format',
        'Review a resume for ATS (Applicant Tracking System) optimization',
        'Create a cover letter based on a resume',
        'Highlight achievements and accomplishments in a resume',
        'Suggest action verbs and keywords for a resume',
        'Provide feedback on the layout and design of a resume',
        'Compare a resume against a job description',
        'Recommend improvements for a LinkedIn profile based on a resume'
        ]
        prompt_categories = {
        'General': general_prompts,
        'Educational': educational_prompts,
        'Legal': legal_prompts,
        'Professional CV/Resume': professional_prompts
        }

        selected_category = st.selectbox('Choose a category', list(prompt_categories.keys()))
        selected_prompt = st.selectbox('Choose the target action prompt', prompt_categories[selected_category])

        # Show language selection only if "Translate" is selected
        if selected_prompt in ['Translate the document to another language', 'Translate legal documents to another language']:
            target_languages = [
                'English', 'Arabic', 'Mandarin Chinese', 'Spanish', 'French', 
                'Portuguese', 'Russian', 'Japanese', 'German', 'Korean', 
                'Vietnamese', 'Turkish', 'Tamil', 'Urdu', 'Italian', 'Dutch'
            ]
            selected_language = st.selectbox('Select your preferred target language for translation', target_languages)

        if st.button("Submit"):
            if st.session_state.document:
                document_chunks = split_document(st.session_state.document)
                st.session_state.document_chunks = document_chunks

                if selected_prompt in ['Translate the document to another language', 'Translate legal documents to another language'] and selected_language:
                    prompt_texts = [f"Please translate the following document from {st.session_state.detected_language} to {selected_language}:\n\n{chunk}" for chunk in document_chunks]
                else:
                    prompt_texts = [f"Please {selected_prompt.lower()} the following document:\n\n{chunk}" for chunk in document_chunks]

                with st.spinner("Generating response..."):
                    asyncio.run(generate_response(prompt_texts))

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        st.error(f"Details: {str(e)}")
