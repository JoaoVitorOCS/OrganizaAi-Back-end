from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("=" * 60)
    print("Iniciando servidor Flask...")
    print(f"Host: {host}")
    print(f"Porta: {port}")
    print(f"Debug: {debug}")
    print(f"Acesse: http://localhost:{port}")
    print("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )