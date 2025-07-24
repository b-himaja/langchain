
#better for locally run the vector embeddinsg instead of a cloud based db like pinecone

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain

if __name__ == '__main__':
    pdf_path = "/home/sumit/Desktop/langchain/intro-to-vector-dbs/vectorstore-in-memory/chainofthought.pdf"
    loader = PyPDFLoader(file_path=pdf_path)
    documents = loader.load()
    text_Splitter = CharacterTextSplitter(chunk_size=1000,chunk_overlap=30,separator="\n")
    docs = text_Splitter.split_documents(documents=documents)

    embeddings = GoogleGenerativeAIEmbeddings(google_api_key=os.environ.get("GOOGLE_API_KEY"), model="models/embedding-001")
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("faiss_index_cot")

    new_vectorstore = FAISS.load_local(
        "faiss_index_cot", embeddings,allow_dangerous_deserialization=True
    )
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
    retrieval_chain = create_retrieval_chain(
        retriever=vectorstore.as_retriever(), combine_docs_chain=combine_docs_chain
    )

    result =retrieval_chain.invoke(input={"input":"Give me the gist of chain of thought in 3 sentences"})
    print(result["answer"])