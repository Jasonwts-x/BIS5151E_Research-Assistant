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
 
    Orchestrates Writer → Reviewer → FactChecker → (Translator) pipeline using CrewAI.
    Supports both default mode (with context) and fallback mode (without context).
    """
 
    def __init__(self, llm):
        """
        Initialize the crew with agents.
 
        Args:
            llm: Language model instance (from Ollama via LangChain)
        """
        self.llm = llm
 
        # Initialize agents
        logger.info("Initializing ResearchCrew agents")
        self.writer = create_writer_agent(llm)
        self.reviewer = create_reviewer_agent(llm)
        self.factchecker = create_factchecker_agent(llm)
        self.translator = create_translator_agent(llm)
        logger.info("ResearchCrew agents initialized successfully")
 
    def run(self, topic: str, context: str, language: str = "en") -> str:
        """
        Execute the research crew workflow.
       
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
 
        # Detect if we have actual context or not
        has_context = self._has_valid_context(context)
 
        if has_context:
            logger.info("Valid context available - using default mode with %d chars", len(context))
            return self._run_default_mode(topic, context, language)
        else:
            logger.warning("No valid context available - using fallback mode")
            return self._run_fallback_mode(topic, language)
 
    def _has_valid_context(self, context: str) -> bool:
        """
        Check if context contains actual documents or is just a placeholder.
        """
        if not context:
            return False
       
        # Check for common "no context" indicators
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
       
        # Check if context is too short (likely just a message)
        if len(context.strip()) < 100:
            logger.debug("Context validation failed: too short (%d chars)", len(context.strip()))
            return False
       
        # Check if context contains source markers (indicating real documents)
        if "SOURCE" not in context:
            logger.debug("Context validation failed: no SOURCE markers found")
            return False
       
        logger.debug("Context validation passed: %d chars with SOURCE markers", len(context))
        return True
 
    def _summarize_sources(self, raw_context: str, topic: str) -> str:
        """
        Extract metadata from sources without duplicates.
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


    def _extract_metadata_simple(self, filename: str, content_preview: str) -> dict:
        """
        Extract metadata using regex - no LLM needed.
        Fast and reliable for common formats.
        """
        import re
    
        # Extract year from filename or content
        year_match = re.search(r'(19|20)\d{2}', filename + content_preview)
        year = year_match.group(0) if year_match else "n.d."
    
        # Extract author from filename (before underscore/dash)
        author_match = re.match(r'^([A-Za-z]+)', filename)
        author = author_match.group(1) if author_match else "Unknown"
    
        # Title from filename (remove extension)
        title = re.sub(r'\.(pdf|txt|md|arxiv)$', '', filename, flags=re.IGNORECASE)
        title = title.replace('_', ' ').replace('-', ' ')
    
        # Try to find better author in content (first 500 chars)
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
 
    def _run_default_mode(self, topic: str, context: str, language: str) -> str:
        """
        Run full pipeline with default fact-checking against provided context.
        Uses Pre-Summarization to speed up processing.
        """
        logger.info("Running DEFAULT MODE - with optimized context")
       
        # 1. OPTIMIZATION STEP: Summarize context first
        optimized_context = self._summarize_sources(context, topic)
       
        # 2. Create tasks with OPTIMIZED context
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
       
        # Add translation if needed
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
        Run full pipeline using general knowledge (no local database context).
        """
        logger.info("Running FALLBACK MODE - using general knowledge")
       
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
       
        factchecker_task = create_factchecker_task(
            agent=self.factchecker,
            reviewer_task=reviewer_task,
            context=""
        )
 
        tasks = [writer_task, reviewer_task, factchecker_task]
 
        # Add translation if needed
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
       
        logger.info("Executing fallback crew with %d tasks", len(tasks))
        result = crew.kickoff()
 
        formatted_output = self._format_output(result, mode="fallback")
 
        logger.info("Fallback crew execution completed. Output length: %d chars", len(formatted_output))
        return formatted_output
 
    def _format_output(self, result, mode: str = "default") -> str:
        """
        Format crew output correctly, preserving citations and CLEANING unwanted artifacts.
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
   
    def _extract_citations_count(self, text: str) -> int:
        """
        Count inline citations in text for debugging.
        """
        import re
        citations = re.findall(r'\[\d+\]', text)
        return len(citations)