import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore


if __name__ =='__main__':
    load_dotenv()
    print("GOOGLE_API_KEY =", os.environ.get("GOOGLE_API_KEY"))

    print("Ingestion")
    loader = TextLoader("/home/sumit/Desktop/langchain/intro-to-vector-dbs/mediumblog1.txt")
    document = loader.load()

    print("splitting")
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts= text_splitter.split_documents(document)
    print(f"created {len(texts)} chunks")

    embeddings = GoogleGenerativeAIEmbeddings(google_api_key=os.environ.get("GOOGLE_API_KEY"), model="models/embedding-001")

    print("ingesting...")
    PineconeVectorStore.from_documents(texts,embeddings,index_name=os.environ["INDEX_NAME"])
    print("Finish")


