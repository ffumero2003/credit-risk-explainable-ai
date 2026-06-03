"""Quick connectivity test for the Claude API."""
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()                 # read .env into environment variables
client = Anthropic()          # automatically picks up ANTHROPIC_API_KEY

response = client.messages.create(
    model="claude-haiku-4-5-20251001",   # cheap, fast model — right-sized for this task
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(response.content[0].text)   # the SDK returns content as a list of blocks