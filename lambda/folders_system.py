import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
folders_table = dynamodb.Table('documentgpt-folders')

def create_folder(user_id, folder_name, parent_id=None):
    """Create a new folder"""
    folder_id = f"folder_{int(datetime.now().timestamp())}"
    
    folder_item = {
        'folder_id': folder_id,
        'user_id': user_id,
        'name': folder_name,
        'parent_id': parent_id,
        'created_at': datetime.now().isoformat(),
        'document_count': 0
    }
    
    folders_table.put_item(Item=folder_item)
    return folder_item

def get_user_folders(user_id):
    """Get all folders for a user"""
    response = folders_table.scan(
        FilterExpression='user_id = :uid',
        ExpressionAttributeValues={':uid': user_id}
    )
    return response.get('Items', [])

def move_document_to_folder(user_id, document_id, folder_id):
    """Move document to folder"""
    users_table = dynamodb.Table('documentgpt-users')
    
    # Update document's folder_id
    users_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET documents.#doc_id.folder_id = :folder_id',
        ExpressionAttributeNames={'#doc_id': document_id},
        ExpressionAttributeValues={':folder_id': folder_id}
    )
    
    return {'success': True}

def get_folder_documents(user_id, folder_id):
    """Get all documents in a folder"""
    users_table = dynamodb.Table('documentgpt-users')
    
    response = users_table.get_item(Key={'user_id': user_id})
    if 'Item' not in response:
        return []
    
    documents = response['Item'].get('documents', {})
    folder_docs = []
    
    for doc_id, doc_data in documents.items():
        if doc_data.get('folder_id') == folder_id:
            folder_docs.append({
                'id': doc_id,
                'name': doc_data.get('name'),
                'type': doc_data.get('type'),
                'created_at': doc_data.get('created_at')
            })
    
    return folder_docs