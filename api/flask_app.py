from utilities import create_app
from routes import process, summary, entities, task, document

app = create_app()

# Register all route providers
process.register_routes(app)
summary.register_routes(app)
entities.register_routes(app)
task.register_routes(app)
document.register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
