from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
from transformers import pipeline

# Initialize the QA pipeline
qa_pipeline = pipeline("question-answering")

# Load the knowledge base from text files in a directory
def load_knowledge_base(directory="knowledge_base"):
    knowledge_base = {}
    
    # Loop through each file in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            # Load the content of each file
            with open(os.path.join(directory, filename), "r") as file:
                topic = filename.replace(".txt", "")  # Use filename (without extension) as topic
                content = file.read()
                knowledge_base[topic] = content
                
    return knowledge_base

# Load the knowledge base (assuming your directory is structured with .txt files)
knowledge_base = load_knowledge_base("knowledge_base")

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Build FAISS index for fast retrieval
all_embeddings = []
topics = []

# Collect embeddings for FAISS
for topic, content in knowledge_base.items():
    topic_embeddings = model.encode(content.split('\n'))  # Embedding for each sentence/paragraph
    all_embeddings.extend(topic_embeddings)  # Flattening all embeddings
    topics.extend([topic] * len(topic_embeddings))  # Storing topic for each embedding

# Convert to numpy array
all_embeddings = np.array(all_embeddings)

# FAISS setup
dimension = all_embeddings.shape[1]  # Ensure this matches the embedding dimensionality
index = faiss.IndexFlatL2(dimension)

# Add the embeddings to FAISS index
index.add(all_embeddings)

# Function to get an answer
def get_answer(question):
    # Encode the question to get its embedding
    question_embedding = model.encode([question])  # This will return a 2D array
    _, I = index.search(question_embedding, k=5)  # Retrieve the top 5 closest matches
    
    # Combine the contexts of the top k matches into a larger context
    context = ' '.join([knowledge_base[topics[i]] for i in I[0]])  # Combine the contexts of the top matches
    
    # Use the QA pipeline to extract answer from context
    result = qa_pipeline(question=question, context=context)
    
    # Check for empty answer and add a fallback response
    if not result['answer']:
        return "I'm sorry, I couldn't find an answer to your question."
    
    return result['answer']

if __name__ == "__main__":
    print("Hello! I'm here to help with loans, investments, and insurance. Ask me anything!")
    
    while True:
        question = input("Your Question: ")
        if question.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        answer = get_answer(question)
        print(f"Answer: {answer}")