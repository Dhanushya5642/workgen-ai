"""
Organization Knowledge Module for AgentX.

This module allows AgentX to learn an organization's official documents
(such as Rules & Regulations, Code of Conduct, Employee Handbook, SOPs, etc.)
and answer user questions strictly based on those documents.

MVP supports only ONE organization at a time — uploading a new document
replaces the previous knowledge base.
"""

from modules.organization_knowledge.orchestrator import OrganizationKnowledgeOrchestrator

__all__ = ["OrganizationKnowledgeOrchestrator"]

