"""
Research Crew Composition Module.

Orchestrates Writer → Reviewer → FactChecker → (Translator) pipeline using CrewAI.
Supports both default mode (with context) and fallback mode (without context).

Architecture:
    Manages sequential agent execution with proper task dependencies.
    Adapts workflow based on context availability and target language.
"""
from __future__ import annotations
 
from fileinput import filename
import logging
import re
from typing import TYPE_CHECKING
 
from crewai import Agent, Crew, Process, Task
 
from ..roles import (
    create_factchecker_agent,
    create_reviewer_agent,
    create_translator_agent,
    create_writer_agent,
)
 
from ..tasks import (
    create_factchecker_task,
    create_reviewer_task,
    create_translator_task,
    create_writer_task,
)
 
logger = logging.getLogger(__name__)
 
 
class ResearchCrew:
    """
    Research Assistant Crew composition.

    Manages the sequential execution of specialized agents and handles 
    context-aware path selection to ensure grounded research output.

    Attributes:
        llm: The Language Model instance used by all agents.
        writer: Agent responsible for initial drafting and citation grounding.
        reviewer: Agent responsible for academic tone and flow.
        factchecker: Agent responsible for cross-referencing output against context.
        translator: Optional agent for multilingual support.
    """
 
    def __init__(self, llm):
        """
        Initialize the ResearchCrew with shared LLM configuration.
 
        Args:
            llm: Language model instance (from Ollama via LangChain)
        """
        self.llm = llm
 
        # Agents are initialized at class level to maintain configuration
        # consistency throughout the lifecycle of the ResearchCrew instance.
        logger.info("Initializing ResearchCrew agents")
        self.writer = create_writer_agent(llm)
        self.reviewer = create_reviewer_agent(llm)
        self.factchecker = create_factchecker_agent(llm)
        self.translator = create_translator_agent(llm)
        logger.info("ResearchCrew agents initialized successfully")
 
    def run(self, topic: str, context: str, language: str = "en") -> str:
        """
        Execute the core research workflow with dynamic mode detection.
       
        Detects whether context is available and adjusts workflow accordingly:
        - WITH context: Full pipeline (Writer → Reviewer → FactChecker)
        - WITHOUT context: Simplified pipeline (Writer only, general knowledge mode)
 
        Args:
            topic: Research topic/question
            context: Retrieved RAG context (may be empty/unavailable message)
            language: Target language
 
        Returns:
            Final output string
        """
        logger.info("Starting crew run for topic: %s", topic)

        # Path selection logic: Default mode requires specific document markers 
        # to prevent the agents from hallucinating when RAG retrieval fails.
        has_context = self._has_valid_context(context)
 
        if has_context:
            logger.info("Valid context available - using default mode with %d chars", len(context))
            return self._run_default_mode(topic, context, language)
        else:
            logger.warning("No valid context available - using fallback mode")
            return self._run_fallback_mode(topic, language)
 
    def _has_valid_context(self, context: str) -> bool:
        """
        Validate if the provided context string contains usable research data.

        Args:
            context: The raw context string to evaluate.

        Returns:
            True if the context passes all sanity checks, False otherwise.
        """
        if not context:
            return False
       
        # We catch explicit strings returned by the RAG pipeline when no vector 
        # matches are found to avoid passing "error messages" as factual context.
        no_context_indicators = [
            "⚠️ NO CONTEXT AVAILABLE ⚠️",
            "NO CONTEXT AVAILABLE",
            "No context available",
            "No documents were retrieved",
        ]
       
        for indicator in no_context_indicators:
            if indicator in context:
                logger.debug("Context validation failed: contains '%s'", indicator)
                return False
       
        # Strings under 100 characters are statistically likely to be metadata 
        # or error messages rather than meaningful academic content.
        if len(context.strip()) < 100:
            logger.debug("Context validation failed: too short (%d chars)", len(context.strip()))
            return False
       
        # Our RAG pipeline strictly enforces 'SOURCE' headers;
        # their absence indicates unformatted or corrupted retrieval.
        if "SOURCE" not in context:
            logger.debug("Context validation failed: no SOURCE markers found")
            return False
       
        logger.debug("Context validation passed: %d chars with SOURCE markers", len(context))
        return True
    
    def _extract_metadata_simple(self, filename: str, content_preview: str) -> dict:
        """
        Perform lightweight metadata extraction using using regex patterns.

        Args:
            filename: Name of the source file.
            content_preview: A subset of document text for pattern matching.

        Returns:
            Dictionary containing extracted 'author', 'year', and 'title'.
        """
        import re
    
        # Extract year from filename or content
        year_match = re.search(r'(19|20)\d{2}', filename + content_preview)
        year = year_match.group(0) if year_match else "n.d."
    
        # Extract author from filename (before underscore/dash).
        author_match = re.match(r'^([A-Za-z]+)', filename)
        author = author_match.group(1) if author_match else "Unknown"
    
        # Cleanup filename artifacts to create a human-readable title fallback.
        title = re.sub(r'\.(pdf|txt|md|arxiv)$', '', filename, flags=re.IGNORECASE)
        title = title.replace('_', ' ').replace('-', ' ')
    
        # Try to find better author in content (first 500 chars).
        author_patterns = [
            r'(?:Author|By):\s*([A-Z][a-z]+)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        for pattern in author_patterns:
            match = re.search(pattern, content_preview, re.MULTILINE)
            if match:
                author = match.group(1).split()[0]  # First surname
                break
    
        return {
            'author': author,
            'year': year,
            'title': title[:100]  # Limit length
        }
   
    def _extract_citations_count(self, text: str) -> int:
        """
        Identify and count formal inline citations within a text string.

        Primarily used as a quality metric to verify if the Writer agent 
        is following grounding constraints by linking facts to sources.

        Args:
            text: The generated summary or research text to analyze for [n] patterns.

        Returns:
            The total integer count of unique or repeating [n] style citations found.
        """
        import re
        citations = re.findall(r'\[\d+\]', text)
        return len(citations)

    def _run_default_mode(self, topic: str, context: str, language: str) -> str:
        """
        Execute the full research pipeline using retrieved local context.
        
        Args:
            topic: The research subject.
            context: Validated RAG context.
            language: Desired output language.

        Returns:
            Formatted final output string.
        """
        logger.info("Running DEFAULT MODE - with optimized context")
       
        # We summarize/clean sources before passing to CrewAI
        # to prevent context window overflow in local LLMs (Ollama).
        optimized_context = self._summarize_sources(context, topic)
       
        writer_task = create_writer_task(
            agent=self.writer,
            topic=topic,
            context=optimized_context,
            mode="default"
        )
       
        reviewer_task = create_reviewer_task(
            agent=self.reviewer,
            writer_task=writer_task
        )
       
        factchecker_task = create_factchecker_task(
            agent=self.factchecker,
            reviewer_task=reviewer_task,
            context=optimized_context
        )
       
        tasks = [writer_task, reviewer_task, factchecker_task]
       
        # Translation is added as a final sequential step 
        # to ensure the research is fully vetted in English first.
        if language != "en":
            translator_task = create_translator_task(
                agent=self.translator,
                factchecker_task=factchecker_task,
                target_language=language
            )
            tasks.append(translator_task)
            agents_list = [self.writer, self.reviewer, self.factchecker, self.translator]
        else:
            agents_list = [self.writer, self.reviewer, self.factchecker]

        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
       
        logger.info("Executing crew with %d tasks", len(tasks))
        result = crew.kickoff()
 
        formatted_output = self._format_output(result, mode="default")
       
        logger.info("Crew execution completed. Output length: %d chars", len(formatted_output))
        return formatted_output
   
    def _run_fallback_mode(self, topic: str, language: str) -> str:
        """
        Execute a reduced pipeline using the LLM's internal general knowledge.
        
        Args:
            topic: The research subject.
            language: Desired output language.

        Returns:
            Formatted final output string.
        """
        logger.info("Running FALLBACK MODE - using general knowledge")
       
        # In Fallback mode, we omit the FactChecker cross-reference task 
        # because there is no local context to check against.
        writer_task = create_writer_task(
            agent=self.writer,
            topic=topic,
            context="",
            mode="fallback"
        )
 
        reviewer_task = create_reviewer_task(
            agent=self.reviewer,
            writer_task=writer_task
        )
 
        tasks = [writer_task, reviewer_task]
        agents_list = [self.writer, self.reviewer]
 
        # Translation is added as a final sequential step if needed.
        if language != "en":
            translator_task = create_translator_task(
                agent=self.translator,
                factchecker_task=reviewer_task,
                target_language=language
            )
            tasks.append(translator_task)
            agents_list.append(self.translator)
        
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
       
        logger.info("Executing fallback crew with %d tasks", len(tasks))
        result = crew.kickoff()
 
        formatted_output = self._format_output(result, mode="fallback")
 
        logger.info("Fallback crew execution completed. Output length: %d chars", len(formatted_output))
        return formatted_output
 
    def _format_output(self, result, mode: str = "default") -> str:
        """
        Post-process agent output to remove artifacts and validate formatting.
        
        Args:
            result: Crew execution result
            mode: "default" or "fallback"
            
        Returns:
            Formatted output string
        """
        logger.debug("Formatting output (mode: %s, result type: %s)", mode, type(result))
       
        try:
            # Extract raw text output from CrewAI result
            if hasattr(result, 'raw'):
                output_text = str(result.raw)
            elif hasattr(result, 'output'):
                output_text = str(result.output)
            else:
                output_text = str(result)
           
            output_text = output_text.strip()
           
            # Remove Agent Instructions from Final Output ---
            lines_to_remove = [

                # Meta-commentary patterns
                "actual complete content",
                "not a summary",
                "expected criteria",
                "you must return",
                "this analysis includes",
                "the text contains",
                "references section",
                "appropriately formatted",
                "citations are formatted",

                # Redundant labels
                "final answer:",
                "here is the",
                "here's the",
                "the following is",
            ]
        
            cleaned_lines = []
            for line in output_text.split('\n'):
                lower_line = line.lower().strip()
            
                # Check if line contains any forbidden patterns
                should_skip = False
                for pattern in lines_to_remove:
                    if pattern in lower_line:
                        should_skip = True
                        break
            
                if not should_skip:
                    cleaned_lines.append(line)
           
                output_text = "\n".join(cleaned_lines).strip()
 
            # Log statistics
            citation_count = self._extract_citations_count(output_text)
            has_references = "## References" in output_text or "## Literaturverzeichnis" in output_text
           
            logger.info(
                "✅ Output formatted: %d chars, %d citations, has_references=%s",
                len(output_text),
                citation_count,
                has_references
            )
           
            # Validation: Warn if no citations in default mode
            if mode == "default" and citation_count == 0:
                logger.warning("⚠️ DEFAULT MODE but no citations [1], [2] found in output!")
           
            if mode == "default" and not has_references:
                logger.warning("⚠️ DEFAULT MODE but no ## References section found!")
           
            return output_text
           
        except Exception as e:
            logger.error("❌ Error formatting output: %s. Using fallback.", e, exc_info=True)
            return str(result)
        
    def _summarize_sources(self, raw_context: str, topic: str) -> str:
        """
        Pre-summarize sources to reduce context size.
        
        Args:
            context: The full context string from the retriever.
            topic: The research topic.
            
        Returns:
            Optimized context string with enriched metadata.
        """
        import re
    
        logger.info("⚡ Extracting metadata from sources...")
    
        # Split by SOURCE markers
        parts = re.split(r'(SOURCE \[\d+\])', raw_context)
    
        seen_sources = set()
        optimized_output = []
        current_header = ""
    
        for part in parts:
            if "SOURCE [" in part:
                current_header = part.strip()
            elif current_header and len(part.strip()) > 50:
                lines = part.strip().split('\n')
                filename = lines[0].strip()

                if filename in seen_sources:
                    current_header = ""
                    continue
                seen_sources.add(filename)

                content = "\n".join(lines[1:]) if len(lines) > 1 else part
            
                # Extract metadata
                metadata = self._extract_metadata_simple(filename, content[:500])
            
                # Format output
                optimized_output.extend([
                    current_header,
                    filename,
                    f"METADATA: {metadata['author']} ({metadata['year']}). {metadata['title']}",
                    "",
                    content[:1000],  # Reduced for speed
                    "-" * 40,
                    ""
                ])
                current_header = ""
    
        result = "\n".join(optimized_output)
        logger.info(f"Metadata extracted: {len(result)} chars")
        return result