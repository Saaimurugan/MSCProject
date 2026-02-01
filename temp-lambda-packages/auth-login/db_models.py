import boto3
from datetime import datetime
import uuid
from typing import Dict, List, Optional

dynamodb = boto3.resource('dynamodb')

class BaseModel:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create_item(self, item: Dict) -> Dict:
        item['created_at'] = datetime.utcnow().isoformat()
        item['updated_at'] = datetime.utcnow().isoformat()
        self.table.put_item(Item=item)
        return item
    
    def get_item(self, key: Dict) -> Optional[Dict]:
        response = self.table.get_item(Key=key)
        return response.get('Item')
    
    def update_item(self, key: Dict, updates: Dict) -> Dict:
        updates['updated_at'] = datetime.utcnow().isoformat()
        update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expression_values = {f":{k}": v for k, v in updates.items()}
        
        response = self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        return response['Attributes']

class User(BaseModel):
    def __init__(self):
        import os
        table_name = os.environ.get('USERS_TABLE', 'msc-evaluate-users-dev')
        super().__init__(table_name)
    
    def create_user(self, email: str, name: str, role: str = 'student') -> Dict:
        user_id = str(uuid.uuid4())
        user = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,  # student, tutor, admin
            'is_active': True
        }
        return self.create_item(user)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        response = self.table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        items = response.get('Items', [])
        return items[0] if items else None

class Template(BaseModel):
    def __init__(self):
        import os
        table_name = os.environ.get('TEMPLATES_TABLE', 'msc-evaluate-templates-dev')
        super().__init__(table_name)
    
    def create_template(self, title: str, subject: str, course: str, 
                       questions: List[Dict], created_by: str) -> Dict:
        template_id = str(uuid.uuid4())
        template = {
            'template_id': template_id,
            'title': title,
            'subject': subject,
            'course': course,
            'questions': questions,
            'created_by': created_by,
            'is_active': True
        }
        return self.create_item(template)
    
    def get_templates_by_subject_course(self, subject: str, course: str) -> List[Dict]:
        response = self.table.scan(
            FilterExpression='subject = :subject AND course = :course AND is_active = :active',
            ExpressionAttributeValues={
                ':subject': subject,
                ':course': course,
                ':active': True
            }
        )
        return response.get('Items', [])

class QuizResult(BaseModel):
    def __init__(self):
        import os
        table_name = os.environ.get('QUIZ_RESULTS_TABLE', 'msc-evaluate-quiz-results-dev')
        super().__init__(table_name)
    
    def save_result(self, user_id: str, template_id: str, student_name: str, 
                   student_id: str, answers: List[Dict], total_score: float) -> Dict:
        result_id = str(uuid.uuid4())
        result = {
            'result_id': result_id,
            'user_id': user_id,
            'template_id': template_id,
            'student_name': student_name,
            'student_id': student_id,
            'answers': answers,
            'total_score': total_score,
            'completed_at': datetime.utcnow().isoformat()
        }
        return self.create_item(result)
    
    def get_user_results(self, user_id: str) -> List[Dict]:
        response = self.table.scan(
            FilterExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        return response.get('Items', [])