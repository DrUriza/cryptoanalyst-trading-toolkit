\# Architecture Overview



CryptoAnalyst is organized into four main modules:



```text

CryptoAnalyst/

&#x20; Chatbot/

&#x20; HMI/

&#x20; MLFramework/

&#x20; TechAnalyze/

High-Level Flow

Market image / chart / data

&#x20;           ↓

&#x20;      TechAnalyze

&#x20;           ↓

&#x20;      MLFramework

&#x20;           ↓

&#x20;          HMI

&#x20;           ↓

&#x20;    Chatbot / Report

Module Responsibilities

TechAnalyze



Responsible for technical analysis, chart structure interpretation, trend analysis, support/resistance identification, and pattern detection.



MLFramework



Responsible for feature processing, model-ready data structures, signal classification support, and data-driven analysis.



HMI



Responsible for the visual interface, dashboards, charts, user interaction, and analysis presentation.



Chatbot



Responsible for explanation, report generation, and natural-language summaries of market analysis.



Portfolio Purpose



This architecture demonstrates the ability to build a modular trading research tool that combines technical analysis, machine learning, visualization, and communication.

