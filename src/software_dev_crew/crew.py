from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileWriterTool

@CrewBase
class SoftwareDevCrew:
    """Software Development crew for building CLI tools, utilities, libraries, and applications"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'],
            allow_delegation=False,
            verbose=True
        )
    
    @agent
    def software_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['software_engineer'],
            allow_delegation=False,
            verbose=True
        )
    
    @agent
    def qa_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['qa_engineer'],
            allow_delegation=True,
            verbose=True,
            tools=[FileWriterTool()]
        )
    

    @task
    def requirements_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['requirements_analysis_task'],
            agent=self.product_manager()
        )

    @task
    def development_task(self) -> Task:
        return Task(
            config=self.tasks_config['development_task'],
            agent=self.software_engineer()
        )

    @task
    def qa_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['qa_review_task'],
            agent=self.qa_engineer()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SoftwareDevCrew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )