from google import genai
from openai import OpenAI
class LLMClient:
    def __init__(self,model_name='deepseek-v3-2-251201'):
        self.client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3",
                             api_key='YOUR_API_KEY_HERE')
        self.model_name = model_name
    def generate(self,prompt:str) -> str:
        completion = self.client.chat.completions.create(
            model = self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
# class LLMClient:
#     def __init__(self,model_name:str = 'gemini-3-flash-preview'):
#         self.client = genai.Client(api_key='YOUR_API_KEY_HERE')
#         self.model_name = model_name
#     def generate(self,prompt:str) -> str:
#         reponse = self.client.models.generate_content(
#             model=self.model_name,
#             contents = prompt
#         )
#         return reponse.text
a = LLMClient()
print(a.generate("写一首关于春天的诗歌"))