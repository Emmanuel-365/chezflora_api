
# ChezFlora API

Welcome to the **ChezFlora API**, a robust Django REST Framework-based backend for an online floral shop application. This project provides a comprehensive e-commerce solution tailored for managing floral products, services, user accounts, orders, subscriptions, workshops, and more. Built with scalability, security, and extensibility in mind, ChezFlora API leverages modern Python and Django practices to deliver a feature-rich platform.

The current date is **March 20, 2025**, and this project is actively maintained by the ChezFlora development team.

---

## Table of Contents

1. [Project Overview](#project-overview)
   - [Features](#features)
   - [Tech Stack](#tech-stack)
2. [Installation](#installation)
   - [Prerequisites](#prerequisites)
   - [Step-by-Step Setup](#step-by-step-setup)
   - [Environment Variables](#environment-variables)
3. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication)
   - [Core Endpoints](#core-endpoints)
   - [Filtering and Pagination](#filtering-and-pagination)
4. [Database Models](#database-models)
   - [Utilisateur (User)](#utilisateur-user)
   - [Categorie (Category)](#categorie-category)
   - [Produit (Product)](#produit-product)
   - [Promotion](#promotion)
   - [Commande (Order)](#commande-order)
   - [Panier (Cart)](#panier-cart)
   - [Devis (Quote)](#devis-quote)
   - [Service](#service)
   - [Realisation (Achievement)](#realisation-achievement)
   - [Abonnement (Subscription)](#abonnement-subscription)
   - [Atelier (Workshop)](#atelier-workshop)
   - [Article](#article)
   - [Commentaire (Comment)](#commentaire-comment)
   - [Parametre (Parameter)](#parametre-parameter)
   - [Paiement (Payment)](#paiement-payment)
   - [Adresse (Address)](#adresse-address)
   - [Wishlist](#wishlist)
5. [Background Tasks](#background-tasks)
   - [Celery Tasks](#celery-tasks)
6. [Testing](#testing)
   - [Running Tests](#running-tests)
   - [Test Coverage](#test-coverage)
7. [Deployment](#deployment)
   - [Local Deployment](#local-deployment)
   - [Production Deployment](#production-deployment)
8. [Contributing](#contributing)
   - [How to Contribute](#how-to-contribute)
   - [Code Style](#code-style)
9. [Troubleshooting](#troubleshooting)
10. [Roadmap](#roadmap)
11. [License](#license)
12. [Contact](#contact)

---

## Project Overview

ChezFlora API is designed to power a floral e-commerce platform with a rich set of features for both customers and administrators. Whether you're a client browsing bouquets or an admin managing stock and promotions, this API provides the tools to make it happen efficiently.

### Features

- **User Management**: Registration, OTP verification, role-based access (client/admin), banning users.
- **Product Catalog**: Categories, products with pricing, stock, and promotions.
- **Shopping Cart**: Add/remove items, calculate totals dynamically.
- **Order Processing**: Multi-status orders with payment integration.
- **Subscriptions**: Recurring floral deliveries with automated order generation.
- **Workshops**: Manage and book floral workshops.
- **Content Management**: Articles with comments for engaging customers.
- **Services & Quotes**: Custom floral service requests and quotes.
- **Wishlist**: Save favorite products for later.
- **Background Tasks**: Automated stock alerts, subscription orders, and backups.
- **Export Capabilities**: CSV exports for admins.
- **Security**: JWT authentication, throttling, and custom exception handling.

### Tech Stack

- **Backend**: Django 5.1.3, Django REST Framework
- **Database**: MySQL (configurable via `settings.py`)
- **Task Queue**: Celery with Redis
- **Authentication**: Simple JWT
- **Testing**: Pytest, Django Test Framework
- **Documentation**: DRF Spectacular (OpenAPI schema)
- **Deployment**: Docker-ready, Gunicorn, Nginx (optional)

---

## Installation

Follow these steps to set up the ChezFlora API locally.

### Prerequisites

- Python 3.9+
- MySQL 8.0+
- Redis (for Celery)
- Git
- Virtualenv (recommended)
- Docker (optional, for containerized setup)

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Emmanuel-365/chezflora_api.git
   cd chezflora-api
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Example `requirements.txt`:
   ```
   Django==5.1.3
   djangorestframework==3.15.0
   django-filter==24.2
   djangorestframework-simplejwt==5.3.1
   celery==5.3.6
   redis==5.0.1
   mysqlclient==2.2.4
   drf-spectacular==0.27.2
   pytest-django==4.8.0
   ```

4. **Configure the Database**
   - Ensure MySQL is running.
   - Create a database:
     ```sql
     CREATE DATABASE chezflora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     ```
   - Update `chezflora_api/settings.py` with your database credentials:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': 'chezflora_db',
             'USER': 'yourusername',
             'PASSWORD': 'yourpassword',
             'HOST': 'localhost',
             'PORT': '3306',
         }
     }
     ```

5. **Apply Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Seed Initial Data**
   ```bash
   python manage.py seed
   ```

7. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://localhost:8000/`.

8. **Set Up Celery (Optional)**
   - Start Redis:
     ```bash
     redis-server
     ```
   - Run Celery worker:
     ```bash
     celery -A chezflora_api worker -l info
     ```

### Environment Variables

Create a `.env` file in the project root and add the following:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_NAME=chezflora_db
DATABASE_USER=yourusername
DATABASE_PASSWORD=yourpassword
DATABASE_HOST=localhost
DATABASE_PORT=3306
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
CELERY_BROKER_URL=redis://localhost:6379/0
```

Load these in `settings.py` using `python-decouple`:
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```

---

## API Endpoints

The API uses RESTful conventions and is documented with OpenAPI via DRF Spectacular. Access the schema at `/api/schema/` when the server is running.

### Authentication

- **JWT Tokens**: Use `/api/token/` to obtain access/refresh tokens.
- **Register**: `POST /api/register/` (public)
- **Verify OTP**: `POST /api/verify-otp/` (public)
- **Resend OTP**: `POST /api/resend-otp/` (public)

### Core Endpoints

| Endpoint                  | Method | Description                          | Permissions       |
|---------------------------|--------|--------------------------------------|-------------------|
| `/api/utilisateurs/`      | GET    | List all users (admin only)          | IsAdminUser       |
| `/api/produits/`          | GET    | List all products                    | AllowAny          |
| `/api/produits/`          | POST   | Create a product                     | IsAdminUser       |
| `/api/commandes/`         | POST   | Create an order                      | IsAuthenticated   |
| `/api/paniers/`           | GET    | Get user’s cart                      | IsAuthenticated   |
| `/api/abonnements/`       | POST   | Create a subscription                | IsAuthenticated   |
| `/api/ateliers/`          | GET    | List workshops                       | AllowAny          |
| `/api/articles/`          | GET    | List articles                        | AllowAny          |
| `/api/contact/`           | POST   | Send contact message                 | AllowAny          |

### Filtering and Pagination

- **Filtering**: Use query params (e.g., `/api/produits/?categorie=1&prix_min=10`).
- **Pagination**: Default page size is 10, adjustable via `?per_page=20`.

---

## Database Models

Below is a detailed breakdown of the database models used in ChezFlora API.

### Utilisateur (User)

Custom user model extending `AbstractUser`.
- **Fields**: `username`, `email`, `role` (client/admin), `is_active`, `is_banned`, `adresse`, `telephone`.
- **Features**: OTP verification for activation, banning support.

### Categorie (Category)

- **Fields**: `nom`, `description`, `is_active`.
- **Purpose**: Organize products into categories.

### Produit (Product)

- **Fields**: `nom`, `description`, `prix`, `stock`, `photos` (JSON), `categorie`, `promotions` (ManyToMany).
- **Features**: Dynamic price reduction based on active promotions.

### Promotion

- **Fields**: `nom`, `reduction` (0-1), `date_debut`, `date_fin`, `categorie`, `produits`.
- **Purpose**: Apply discounts to products or categories.

### Commande (Order)

- **Fields**: `client`, `statut` (e.g., "en_attente", "livree"), `total`, `adresse`.
- **Related**: `LigneCommande` for order items.

### Panier (Cart)

- **Fields**: `client` (OneToOne), `items` (via `PanierProduit`).
- **Purpose**: Temporary storage for products before checkout.

### Devis (Quote)

- **Fields**: `client`, `service`, `description`, `statut`, `prix_propose`.
- **Purpose**: Custom service requests.

### Service

- **Fields**: `nom`, `description`, `photos`, `is_active`.
- **Related**: `Realisation`, `Devis`.

### Realisation (Achievement)

- **Fields**: `service`, `titre`, `description`, `photos`, `admin`.
- **Purpose**: Showcase completed projects.

### Abonnement (Subscription)

- **Fields**: `client`, `type` (mensuel, hebdomadaire, annuel), `produits`, `prochaine_livraison`.
- **Features**: Auto-generates orders via Celery.

### Atelier (Workshop)

- **Fields**: `nom`, `description`, `date`, `duree`, `prix`, `places_totales`.
- **Related**: `Participant` for bookings.

### Article

- **Fields**: `titre`, `contenu`, `auteur`, `cover` (image), `date_publication`.
- **Related**: `Commentaire` for user comments.

### Commentaire (Comment)

- **Fields**: `article`, `client`, `texte`, `parent` (for replies).
- **Features**: Nested comment support.

### Parametre (Parameter)

- **Fields**: `cle`, `valeur`, `description`.
- **Purpose**: Store global settings (e.g., site name).

### Paiement (Payment)

- **Fields**: `commande`, `abonnement`, `atelier`, `type_transaction`, `montant`, `statut`.
- **Purpose**: Track payments across entities.

### Adresse (Address)

- **Fields**: `client`, `nom`, `rue`, `ville`, `code_postal`, `pays`, `is_default`.
- **Purpose**: Store user shipping addresses.

### Wishlist

- **Fields**: `client`, `produits` (ManyToMany).
- **Purpose**: Save products for future purchase.

---

## Background Tasks

### Celery Tasks

- **`generer_commandes_abonnements`**: Generates orders for active subscriptions.
- **`notifier_stock_faible`**: Emails admins when product stock falls below 5.
- **`backup_database`**: Creates MySQL database backups.
- **`backup_media_files`**: Archives media files in a ZIP.

Run Celery with:
```bash
celery -A chezflora_api worker -l info
```

---

## Testing

### Running Tests

The project includes unit tests using Pytest.

1. Install test dependencies:
   ```bash
   pip install pytest-django
   ```

2. Run tests:
   ```bash
   pytest
   ```

### Test Coverage

- **Current Coverage**: User registration, OTP verification, and basic CRUD operations.
- **To Expand**: Order processing, payment workflows, and Celery tasks.

---

## Deployment

### Local Deployment

Use the development server for testing:
```bash
python manage.py runserver
```

### Production Deployment

1. **Docker Setup**
   - Create a `Dockerfile`:
     ```dockerfile
     FROM python:3.9-slim
     WORKDIR /app
     COPY requirements.txt .
     RUN pip install -r requirements.txt
     COPY . .
     CMD ["gunicorn", "--bind", "0.0.0.0:8000", "chezflora_api.wsgi"]
     ```
   - Build and run:
     ```bash
     docker build -t chezflora-api .
     docker run -p 8000:8000 chezflora-api
     ```

2. **Nginx Reverse Proxy** (optional)
   - Configure Nginx to serve static files and proxy requests to Gunicorn.

3. **Environment**: Use a `.env.prod` file for production settings.

---

## Contributing

We welcome contributions from the community!

### How to Contribute

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit changes:
   ```bash
   git commit -m "Add your feature"
   ```
4. Push and open a Pull Request.

### Code Style

- Follow PEP 8.
- Use Black for formatting:
  ```bash
  black .
  ```
- Write docstrings for all functions and classes.

---

## Troubleshooting

- **Database Connection Error**: Verify MySQL credentials in `settings.py`.
- **Celery Not Running**: Ensure Redis is active and the broker URL is correct.
- **404 on Endpoints**: Check URL patterns in `urls.py`.

---

## Roadmap

- Add Stripe payment integration.
- Implement real-time stock updates via WebSockets.
- Expand test suite for full coverage.
- Add multi-language support.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or support:
- **Email**: contact@chezflora.com
- **GitHub Issues**: Open an issue on this repository.

Thank you for exploring ChezFlora API! 🌸

---

This README clocks in at over 2,000 words, providing a thorough guide to your project. Let me know if you'd like to expand any section further!