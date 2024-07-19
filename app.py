import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from transformers import T5Tokenizer, T5ForConditionalGeneration, pipeline
import torch
import base64
import tempfile

checkpoint = "LaMini-Flan-T5-248M" 
tokenizer = T5Tokenizer.from_pretrained(checkpoint)

# Load the model with low memory usage on CPU
baseModel = T5ForConditionalGeneration.from_pretrained(
    checkpoint, 
    low_cpu_mem_usage=True
).cpu()

def fileProcessing(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    texts = text_splitter.split_documents(pages)
    finalTexts = ""
    for text in texts:
        finalTexts += text.page_content
    return finalTexts

def llm_pipeline(file_path):
    pipeSum = pipeline(
        'summarization',
        model=baseModel,
        tokenizer=tokenizer,
        framework='pt',
        device=0 if torch.cuda.is_available() else -1,
        max_length=500,
        min_length=200
    )
    input_text = fileProcessing(file_path)
    summary = pipeSum(input_text)
    summary_text = summary[0]['summary_text']
    return summary_text

@st.cache_data
def displayPDF(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    pdfDisplay = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdfDisplay, unsafe_allow_html=True)

# Streamlit
st.set_page_config(layout='wide', page_title="Doc Summarizer")

def main():
    st.title('Summarizer')
    uploadedFile = st.file_uploader("Upload your PDF file here!", type=['pdf'])
    
    if uploadedFile is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploadedFile.read())
            temp_file_path = temp_file.name

        displayPDF(temp_file_path)
        
        if st.button("Summarize"):
            summary = llm_pipeline(temp_file_path)
            left, right = st.columns(2)
            with left:
                st.info("Uploaded PDF!")
                displayPDF(temp_file_path)
            with right:
                st.info("Summary:")
                st.success(summary)
                

if __name__ == '__main__':
    main()
