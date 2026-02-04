from app.config import client, DEPLOYMENT_NAME
import time

def stream_response(system_prompt: str, user_prompt: str, delay: float = 0.05):
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        stream=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    for update in response:
        if update.choices:
            content = update.choices[0].delta.content or ""
            if content:
                time.sleep(delay)   # 👈 throttle speed
                yield content
