from utilities import create_app
from routes import process, summary

app = create_app()

# Register all route providers
process.register_routes(app)
summary.register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
