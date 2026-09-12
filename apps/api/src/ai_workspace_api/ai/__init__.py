"""AI provider abstraction: embeddings, chat, structured output, tools.

All provider-specific code is confined to this package and reached through
an interface, so no vendor detail leaks into services or routers.
"""
