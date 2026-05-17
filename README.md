# TrendSerpAPI

A comprehensive Django-based web application for analyzing Google Trends data with Django and template integration, featuring advanced capabilities including user authentication, subscription management, search history tracking, and interactive data visualizations.

## 🚀 Features

### Core Functionality
- **Google Trends Search**: Search and analyze trends data with customizable parameters
- **Interactive Charts**: Dynamic visualizations using Matplotlib and Plotly
- **Multi-Region Support**: Search trends across all available countries and regions
- **Time Range Analysis**: Flexible time period selection for trend analysis
- **Platform Filtering**: Filter trends by web search, image search, news, etc.

### User Management
- **User Authentication**: Secure login/registration system
- **Google OAuth Integration**: Sign in with Google using OAuth 2.0
- **User Profiles**: Customizable user profiles with photo upload
- **Session Management**: Secure session handling with configurable timeouts

### Search & History
- **Search History**: Complete tracking of user search activities
- **Search Management**: View, organize, and delete search history entries
- **Bulk Operations**: Select and delete multiple search entries
- **Export Functionality**: Export search history to PDF format
- **Real-time Updates**: AJAX-powered operations without page reloads

### Subscription System
- **Tiered Plans**: Free, Basic, and Premium subscription tiers
- **Stripe Integration**: Secure payment processing with Stripe
- **Search Limits**: Configurable search limits per plan type
- **Subscription Management**: Cancel and manage subscriptions
- **Plan Upgrades**: Seamless plan upgrade functionality

### Saved Searches (Advanced)
- **Search Collections**: Organize searches into custom collections
- **Favorites System**: Mark important searches as favorites
- **Search Notes**: Add custom notes and tags to saved searches
- **View Tracking**: Track search view counts and last accessed dates
- **Result Snapshots**: Store search result snapshots for comparison

### Communication
- **Contact System**: Built-in contact form for user support
- **Message Management**: Admin interface for managing contact messages
- **Email Notifications**: Automated email notifications for contact submissions
- **Message History**: Users can view their previous contact messages

## 🛠️ Technology Stack

- **Backend**: Django 5.2.1
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: Django AllAuth with Google OAuth
- **Payments**: Stripe API integration
- **Data Visualization**: Matplotlib, Plotly
- **Data Processing**: Pandas, NumPy
- **API Integration**: SerpAPI for Google Trends data
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Styling**: SASS with multiple theme support

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)
- Stripe account (for payment processing)
- SerpAPI key (for Google Trends data)
- Google OAuth credentials (for social authentication)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TrendSerpAPI
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   SERPAPI_KEY=your-serpapi-key
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
   ```

5. **Run database migrations**
   ```bash
   cd SerpApi-Search-Trends
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser account**
   ```bash
   python manage.py createsuperuser
   ```

7. **Fix Google OAuth provider (if needed)**
   ```bash
   python manage.py fix_google_provider
   ```

8. **Start the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000`

## 🔑 Configuration

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://yourdomain.com/accounts/google/login/callback/` (for production)

### Stripe Setup
1. Create a [Stripe account](https://stripe.com/)
2. Get your API keys from the Stripe dashboard
3. Configure webhook endpoints for subscription management

### SerpAPI Setup
1. Sign up for [SerpAPI](https://serpapi.com/)
2. Get your API key from the dashboard
3. Add the key to your environment variables

## 📁 Project Structure

```
TrendSerpAPI/
├── SerpApi-Search-Trends/
│   ├── GoogleTrendsAPI/          # Main project settings
│   ├── accounts/                 # User authentication app
│   ├── trends/                   # Core trends functionality
│   ├── theme/                    # UI themes and styling
│   ├── templates/                # HTML templates
│   ├── static/                   # Static files (CSS, JS, images)
│   ├── media/                    # User uploaded files
│   └── manage.py                 # Django management script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🎯 Usage

### Basic Search
1. Register an account or sign in with Google
2. Navigate to the search page
3. Enter your search term
4. Select region, time range, and platform
5. View interactive charts and data


## 🔒 Security Features

- CSRF protection on all forms
- User input validation and sanitization
- Secure session management
- SQL injection prevention through Django ORM
- XSS protection with template escaping
- Secure payment processing with Stripe

## 🎨 Themes

The application supports multiple themes:
- Dark Theme (default)
- Light Theme
- Blue Theme
- Semi-Dark Theme
- Bordered Theme

## 📊 API Integration

- **SerpAPI**: For fetching Google Trends data
- **Stripe API**: For payment processing and subscription management
- **Google OAuth API**: For social authentication


## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added Google OAuth integration
- **v1.2.0** - Implemented subscription system
- **v1.3.0** - Added saved searches and collections
- **v1.4.0** - Enhanced contact system and admin features

---

**Built with ❤️ using Django and modern web technologies**
