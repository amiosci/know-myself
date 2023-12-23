from flask import jsonify, Flask

from doc_store import disk_store


def register_routes(app: Flask):
    @app.get("/entities/<hash>")
    def get_entities(hash: str):
        store = disk_store.default_store()
        entity_relations = store.load_entity_relations(hash)
        return jsonify([x.model_dump() for x in entity_relations])
