#init: create a document object with all the files
from llama_index.core import StorageContext, load_index_from_storage, SimpleDirectoryReader, GPTVectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, FilterCondition, ExactMatchFilter, MetadataFilter

from database import db
from models import Files

import os

metadata_fn = lambda filename: {'file_name' : filename}

def force_create_embedding(storage_path, file_id, user_id, file_name):
    #forces the creation of the embedding for the file, by either creating the index or overwriting it

    doc_embedding_storage_path = os.path.join(storage_path, str(file_id)+ "_embeddings")
    pathToDocument = os.path.join(storage_path, str(user_id), str(file_id) + "_" + file_name)
    
    document = SimpleDirectoryReader(input_files=[pathToDocument], file_metadata=metadata_fn).load_data()
    
    index = GPTVectorStoreIndex.from_documents(documents=document)
    index.storage_context.persist(persist_dir=doc_embedding_storage_path) 

def create_all_unexisting_embedding(storage_path):
    #to be called within the app context
    #to be run at the start of the app

    #this function will create the embeddings for all the files that don't have one and for the presentation file
    #it checks if the embedding structure exists, if not, it creates it
    #it might not catch a currupted index

    files = db.session.query(Files.id, Files.user_id, Files.file_name).all()

    #creates the presentation index
    
    doc = SimpleDirectoryReader(input_files=["Presentation.txt"], file_metadata=metadata_fn).load_data()
    index = GPTVectorStoreIndex.from_documents(doc)
    index.storage_context.persist(persist_dir=os.path.join(storage_path, "Presentation_embeddings"))
    #-- end of presentation index creation 

    for file in files:
        file_id, user_id, file_name = file
        doc_embedding_storage_path = os.path.join(storage_path, str(file_id)+ "_embeddings")

        #try to load the index if it already exists
        try:
            storageContext = StorageContext.from_defaults(persist_dir=doc_embedding_storage_path)  
            print("Index found for filecode", file_id)
        except:
            print("No index found for filecode", file_id, ". Creating one now")
            force_create_embedding(storage_path, file_id, user_id, file_name)  

def getMergedIndexWithFileIds(storage_path, file_ids):
#input: 
#   storage_path: String, the path to the embeddings storages
#   file_ids: List[Int], the list of file ids whose embeddings we want to merge
#precondition: 
#   the embeddings for the file_ids exist
#   the files won't get checked for authorization here
#output:
#   index: llama_index.core.indices.vector_store.base.VectorStoreIndex, 
#       the merged index of the embeddings of the files or just the presentation index if no correct embeddings are found
#   unavailable_files: [Int], the list of files whose embeddings were not found or corrupted. 
#       If all the embeddings are found, it will be an empty list
    
    #create the base index with the presentation.txt file
    storageContext = StorageContext.from_defaults(persist_dir=os.path.join(storage_path, "Presentation_embeddings"))
    index = load_index_from_storage(storageContext)
    
    unavailable_files = []
    for file_id in file_ids:
        doc_embedding_storage_path = os.path.join(storage_path, str(file_id)+ "_embeddings")
        try:
            storageContext = StorageContext.from_defaults(persist_dir=doc_embedding_storage_path)  
            
            #insert the embedded nodes of the document inside the index
            index.insert_nodes(load_index_from_storage(storageContext).docstore.docs.values())
        except:
            unavailable_files.append(file_id)
            print("No index found, or index corrupted for filecode", file_id, ". Skipping it")
            continue

    return index, unavailable_files

