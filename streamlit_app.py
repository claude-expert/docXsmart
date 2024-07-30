import streamlit as st
from ai71 import AI71
import chardet
import filetype
import PyPDF2

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
        background-color: #ffffff;
    }
    .sidebar .sidebar-content {
        background-color: #1034A6;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #2454FF;
    }
    .stChatMessage--assistant {
        background-color: #e0e0e0;
    }
    .stChatMessage--user {
        background-color: #e0e0e0;
    }
    .title {
        color: #1034A6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar
#st.sidebar.image("assets/docXmart.png", use_column_width=True)
st.sidebar.write("""
**docXmart📃** is your intelligent multilingual assistant for all document-related tasks.
""")

st.sidebar.header("How to Use docXmart📃")
st.sidebar.write("""
1. **Upload Your Document**:
   - Provide a document in .txt, .md, .pdf, or .docx format.
   - Describe what you need help with (e.g., summary, important highlights, translation).

2. **Submit the Information**:
   - Use the input field to enter your instructions.

3. **Get a Response**:
   - docXmart will process your input and generate a detailed response based on your instructions.

4. **Review and Take Action**:
   - Read the response provided by docXmart and follow the suggested steps.
""")
st.sidebar.markdown("### Social Links:")
st.sidebar.write("🔗 [GitHub](https://www.github.com)")

# Show title and description.
st.markdown('<h1 class="title">docXmart📃</h1>', unsafe_allow_html=True)
st.write(
    "This is docXmart, your multilingual assistant that helps with summarizing documents, highlighting important points, translating languages, and more."
)

# Create a session state variable to store the chat messages. This ensures that the
# messages persist across reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []
    instruction = "Hi! This is docXmart. Please upload your document and mention what you need help with. For example; 'Please summarize this document' or 'Translate this document to French'."
    st.session_state.messages.append({"role": "assistant", "content": instruction})

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Let the user upload a file via `st.file_uploader`.
# uploaded_file = st.file_uploader(
#     "Upload a document (.txt , .md , .docx or .pdf)", type=("txt", "md", "pdf", "docx")
# )

# Ask the user for a question via `st.text_area`.
# question = st.text_area(
#     "What do you need help with regarding the document?",
#     placeholder="Can you give me a short summary?",
#     disabled=not uploaded_file,
# )

uploaded_file = st.file_uploader(
    "Upload a document (.txt , .md , .docx or .pdf)", type=("txt", "md", "pdf", "docx")
)


document = ""
if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            st.write("PDF")
        else:
            # Detect encoding
            raw_data = uploaded_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            if encoding is not None:#if confidence > 0:
                document = raw_data.decode(encoding)
            else:
                st.write("here")
        st.success("File uploaded and decoded successfully!")
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}") 

# if uploaded_file and question:
#     # Process the uploaded file and question.
#     document = uploaded_file.read().decode()
    # messages = [
    #     {
    #         "role": "user",
    #         "content": f"Here's a document: {document} \n\n---\n\n {question}",
    #     }
    # ]

    # Generate a response using the AI71 API.
    # with st.spinner("Generating response..."):
    #     try:
    #         response = client.chat.completions.create(
    #             model="tiiuae/falcon-180b-chat",
    #             messages=messages
    #         )

    #         # Collect and concatenate response chunks
    #         if response.choices and response.choices[0].message:
    #             full_response = response.choices[0].message.content

    #             # Stream the full response to the chat using `st.write`
    #             with st.chat_message("assistant"):
    #                 st.markdown(full_response)

    #             st.session_state.messages.append({"role": "assistant", "content": full_response})
    #     except Exception as e:
    #         st.error(f"An error occurred: {e}")

# Creating a dropdown list
options = ['English', 'Arabic', 'Spanish', 'French', 'Dutch', 'Urdu']
selected_option = st.selectbox('Select Language',options)

# # Display the selected option
# st.write('You selected:', selected_option)

# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if prompt := st.chat_input("What do you need help with regarding your document?"):
    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    messages = [
        {
            "role": "user",
            "content": f"Here's a document: {document} \n\n---\n\n {prompt}",
        }
    ]
    # Generate a response using the AI71 API.
    with st.spinner("Generating response..."):
        try:
            response = client.chat.completions.create(
                model="tiiuae/falcon-180b-chat",
                messages=[{"role": "user", "content": prompt}]
            )

            # Collect and concatenate response chunks
            if response.choices and response.choices[0].message:
                full_response = response.choices[0].message.content

                # Stream the full response to the chat using `st.write`
                with st.chat_message("assistant"):
                    st.markdown(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"An error occurred: {e}")
# '''
# # Done 
# # 1. removed the text area, api should be called once for the doc
# # 2. decode issue because of the images, gifs in the doc
# # 3. dropdown option for the user, which lang to be converted in
# To Dos,
# 1. language translation eg. what language this doc is in?
# 2. find Python library that can read images and text
# '''
