import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw - Automated Website Agency Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos:
  init                  Inicializar base de datos
  scrape                Scraper negocios en Google Maps
  worker                Iniciar Celery worker (procesa tareas)
  dashboard             Iniciar dashboard web en http://localhost:8001

Ejemplos:
  python main.py init
  python main.py scrape --query "plomero" --ciudad "Mar del Plata" --max 50
  python main.py worker
  python main.py dashboard
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    # Init DB
    subparsers.add_parser("init", help="Inicializar base de datos")

    # Scraper
    scrape_parser = subparsers.add_parser("scrape", help="Scraper Google Maps")
    scrape_parser.add_argument("--query", required=True, help='Rubro a buscar. Ej: "plomero"')
    scrape_parser.add_argument("--ciudad", required=True, help='Ciudad. Ej: "Mar del Plata"')
    scrape_parser.add_argument("--max", type=int, default=50, help="Maximo de resultados (default: 50)")
    scrape_parser.add_argument("--campana", type=int, default=None, help="ID de campaña (opcional)")

    # Dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Iniciar dashboard web")
    dash_parser.add_argument("--port", type=int, default=8001, help="Puerto (default: 8001)")
    dash_parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")

    # Worker
    worker_parser = subparsers.add_parser("worker", help="Iniciar Celery worker")
    worker_parser.add_argument("--concurrency", type=int, default=4, help="Workers paralelos (default: 4)")

    args = parser.parse_args()

    if args.command == "init":
        from db.database import init_db
        init_db()
        print("Base de datos inicializada correctamente.")
        print("Proximos pasos:")
        print("  1. Configurar .env con tus API keys")
        print("  2. Iniciar Redis: docker compose up -d")
        print("  3. Iniciar worker: python main.py worker")
        print("  4. Scraper: python main.py scrape --query 'plomero' --ciudad 'Mar del Plata'")

    elif args.command == "scrape":
        from workers.scraper import run_scraper
        print(f"Iniciando scraping: '{args.query}' en '{args.ciudad}' (max: {args.max})")
        result = run_scraper.delay(args.query, args.ciudad, args.max, args.campana)
        print(f"Tarea encolada: {result.id}")
        print("Monitorea el progreso en: http://localhost:8001")

    elif args.command == "dashboard":
        import uvicorn
        print(f"Iniciando dashboard en http://{args.host}:{args.port}")
        uvicorn.run("dashboard.app:app", host=args.host, port=args.port, reload=True)

    elif args.command == "worker":
        import subprocess
        cmd = [
            "celery", "-A", "workers.celery_app", "worker",
            "--loglevel=info",
            f"--concurrency={args.concurrency}",
        ]
        print(f"Iniciando Celery worker (concurrency={args.concurrency})")
        subprocess.run(cmd)

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
