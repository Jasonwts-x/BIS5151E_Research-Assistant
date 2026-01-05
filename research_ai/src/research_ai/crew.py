from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.llm import LLM
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ResearchAi:
    """
    Research AI Crew
    - Writer: erstellt den ersten Entwurf
    - Reviewer: prüft Struktur, Argumentation und Stil
    - Fact Checker: überprüft Aussagen und Referenzen
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    # --------------------
    # Gemeinsame LLM-Definition (Ollama, lokal, kostenlos)
    # --------------------
    def _ollama_llm(self) -> LLM:
        return LLM(
            model="ollama/llama3.2:3b",
            base_url="http://localhost:11434",
            temperature=0.2
        )

    # --------------------
    # Agents
    # --------------------
    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=self._ollama_llm(),
            verbose=True
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer"],
            llm=self._ollama_llm(),
            verbose=True
        )

    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["fact_checker"],
            llm=self._ollama_llm(),
            verbose=True
        )

    # --------------------
    # Tasks
    # --------------------
    @task
    def draft_task(self) -> Task:
        return Task(
            config=self.tasks_config["draft_task"]
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config["review_task"]
        )

    @task
    def fact_check_task(self) -> Task:
        return Task(
            config=self.tasks_config["fact_check_task"],
            output_file="final_report.md"
        )

    # --------------------
    # Crew
    # --------------------
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
