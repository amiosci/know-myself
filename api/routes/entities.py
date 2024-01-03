from flask import jsonify, Flask

from content_workflow import DocumentEntitiesContainer, Context


def register_routes(app: Flask):
    @app.get("/entities/<hash>")
    async def get_entities(hash: str):
        content_retriever = DocumentEntitiesContainer()
        context = Context(hash=hash)
        if content_retriever.has_processed(context):
            entity_relations = await content_retriever.get_output_type(context)
            return jsonify([x.model_dump() for x in entity_relations])

        return []
