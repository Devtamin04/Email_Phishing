"""PhishLens Edu - explainable, multimodal phishing risk analysis for schools.

Builds on the KD-BiLSTM text detector of Eskandarian et al. (JISA 2026) and adds analysis
of sender, links, images (OCR + QR) and attachments, a 0-100 risk level with reasons, and
a robustness study against LLM-rewritten / image- / QR- / attachment-borne phishing.
"""
