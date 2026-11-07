from backend.chains.rag_chain import ask_question

response = ask_question("What rights do data subjects have under this GDPR policy?")
print("Answer:", response)
