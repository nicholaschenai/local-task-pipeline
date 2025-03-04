# Local tasks pipeline

A locally hosted pipeline for automating tasks.
My submission to the smol hackathon for smol models,
featuring groq, JigsawStack and Menlo Research, 
and hosted by Antler.

## Intro
### Motivation: why smol models?
- I, like everyone else, *have no time* and want to leverage AI to automate tasks
- My tasks are in a notebook (Obsidian md files), sometimes unstructured
- If AI were to read my notebook for task extraction, it needs to be local for privacy
    - It is a pain to maintain a 'public notebook' and 'private notebook' -- when I write notes, I want to focus on the writing and not some privacy classification
- Local models need to be smol in order to run on my machine

### Architecture
- **Ingestion**: from raw data to structured tasks
- **Monitoring / Human-in-the-loop**: locally-hosted monitoring and confirmation / editing of tasks
    - Need human in the loop instead of automatically sending tasks to internet for execution, as initial extraction can be erroneous (observed when using local models on my notes)
        - False positives: non-tasks gets framed as tasks
        - Misclassification: e.g. coding task gets framed as a web research task
        - Incomplete specification: tasks do not contain enough information for completion
        - Data leak: Personal data from notebook gets extracted into a task
    - Since such automations can perform more tasks than I can, I need a simple way to keep track of the task execution status (e.g. complete, pending, failed) for potential follow-ups
- **Orchestration / Execution**: execute tasks. This is where internet services can come in if needed

### Stack
For the hackathon, I focused on Obsidian md files as the data source and web research service for execution. More sources and services can be added in the future.

#### **Ingestion**
deepseek-r1-distill-llama-70b on Groq via LangChain as my hackathon laptop is not powerful enough.

Outside of the hackathon, I run deepseek-r1:14b via Ollama locally on my desktop and it works decently well with occasional errors mentioned above. 
Will test out Jan AI and other AI engines for better optimizations.

#### **Monitoring / Human-in-the-loop**
Vikunja for project management, mainly their Kanban.
Choice was arbitrary -- I've been testing out various self-hosted project management tools to find the best fit for my needs and decided to test out a new one for this hackathon.

Requirements:
- Locally-hosted
- Have API so tasks can be programmatically updated

Good to have:
- Multi-select and edit (e.g. delete, tag, update status). This is surprisingly rare in self-hosted tools (including Vikunja)
- Mobile app with offline support so I can update tasks on the go
- Sync with other devices on local network

#### **Orchestration / Execution**
JigsawStack's web search API

## Setup
### Python env

```
conda create -n local-tasks-pipeline python=3.11.5
conda activate local-tasks-pipeline
pip install -r requirements.txt
```

### Task management
- Setup [Vikunja](https://github.com/go-vikunja/vikunja) locally (ideally via Docker) and get an API key.
- We use the default Inbox as the project
- In the Kanban view, create 2 more buckets: A 'confirmed' bucket (for tasks which you have reviewed and are ready to be executed) and a 'done' bucket (for tasks which the services have completed)
- Now we want to get some important variables. Create a test task in the 'confirmed' bucket. Then run `test_kanban.py` in `tests` folder
    - When the projects are first listed, under project id `1` (Inbox) view 4 (Kanban), you can find the `done_bucket_id`. This repo sets it to `5` so if yours is different, change it in `test_kanban.py` and the parameter of `update_task_with_results` in `scripts/task_execution.py`
    - When the `=== Testing View Tasks ===` is printed, look for the `bucket_id` of the test task you created in the 'confirmed' bucket. this is the one to be used in `get_confirmed_tasks` in `scripts/task_execution.py` if different from default `4`

### Config
Copy `local_config_example.py` to `local_config.py`, edit the latter with your
- Kanban host URL
- Directory of markdown files
- Model to use for task extraction
- API keys for Kanban, JigsawStack, Groq

## Usage
Run
```
python scripts/task_extraction.py
```
This will extract tasks from the markdown files and save them to the first column of the Kanban board.

Check that the task description reflects what should be the instructions for the web search, else edit it. Then, move it to the 'confirmed' bucket to confirm that it is ready for execution.

Then run

```
python scripts/task_execution.py
```

This will execute the web search and update the task with the results in the description. The task will be moved to the 'done' bucket.

## Future work
- Ingestion: 
    - more task sources, e.g. docs, emails, etc.
    - for context to help task execution, e.g. codebases, agentic RAG
    - Prioritization of tasks, planning (e.g. critical path)
    - structured extraction (e.g. via Ollama's structured output or Outlines library)
- Monitoring / Human-in-the-loop
    - continue finding better tools or build custom ones
- Orchestration / Execution: 
    - more services
        - JigsawStack: web scraping, summarization, image generation, STT, TTS
            - Agentic web research via JigsawStack's web search API as a tool in LangChain for agents
        - Coding (e.g. MetaGPT, OpenHands)
        - browser automation for web tasks
    - Integrate with workflow management tools (e.g. n8n, airflow) for further automation and more complex service integrations
        - e.g. cron jobs, conditional execution, task dependencies


I'll be releasing more of my notes on productivity tools [here](https://github.com/nicholaschenai/productivity-tools) as I gradually clean them up.

I'll also be open-sourcing the future work, so stay tuned!
