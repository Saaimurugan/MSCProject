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

class Template(BaseModel):
    def __init__(self):
        import os
        table_name = os.environ.get('TEMPLATES_TABLE', 'msc-evaluate-templates-dev')
        super().__init__(table_name)
    
    def create_template(self, title: str, subject: str, course: str, 
                       questions: List[Dict]) -> Dict:
        template_id = str(uuid.uuid4())
        template = {
            'template_id': template_id,
            'title': title,
            'subject': subject,
            'course': course,
            'questions': questions,
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
    
    def save_result(self, template_id: str, session_id: str, answers: List[Dict], 
                   total_score: float, correct_count: int, total_questions: int) -> Dict:
        result_id = str(uuid.uuid4())
        result = {
            'result_id': result_id,
            'session_id': session_id,
            'template_id': template_id,
            'answers': answers,
            'total_score': total_score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'completed_at': datetime.utcnow().isoformat()
        }
        return self.create_item(result)
    
    def get_session_results(self, session_id: str) -> List[Dict]:
        response = self.table.scan(
            FilterExpression='session_id = :session_id',
            ExpressionAttributeValues={':session_id': session_id}
        )
        return response.get('Items', [])