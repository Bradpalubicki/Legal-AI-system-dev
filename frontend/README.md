# Legal AI System - Frontend

A comprehensive Next.js 14 frontend application with built-in legal compliance, attorney verification, and professional responsibility features for the Legal AI System.

## 🏗️ Architecture

### Tech Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom legal/compliance color schemes
- **UI Components**: Radix UI primitives with custom compliance components
- **Forms**: React Hook Form + Zod validation
- **State Management**: Custom hooks with React Context
- **HTTP Client**: Axios with automatic token refresh
- **Authentication**: JWT-based with refresh tokens

### Key Features
- ✅ **Built-in Legal Compliance**: Automatic disclaimer management and terms acceptance
- ✅ **Attorney Verification**: Bar number verification with credential checking
- ✅ **Professional Responsibility**: Ethics compliance tracking and monitoring
- ✅ **Forced Compliance**: Blocking UI for non-compliant users
- ✅ **Audit Trail**: Complete logging of compliance actions
- ✅ **Multi-Role Support**: Attorney, Paralegal, Pro Se, Client roles
- ✅ **Accessibility**: WCAG 2.1 AA compliant components
- ✅ **Security**: CSP headers, XSS protection, CSRF prevention

## 📁 Project Structure

```
src/
├── app/                          # Next.js App Router pages
│   ├── auth/                     # Authentication pages
│   │   ├── login/               # Login page with legal warnings
│   │   ├── register/            # Registration with terms acceptance
│   │   └── verify-attorney/     # Attorney verification flow
│   ├── compliance/              # Compliance management pages
│   │   └── terms-acceptance/    # Forced terms acceptance
│   ├── dashboard/               # Main dashboard
│   ├── documents/               # Document management
│   └── layout.tsx               # Root layout with providers
├── components/                  # Reusable UI components
│   └── compliance/              # Compliance-specific components
│       ├── DisclaimerBanner.tsx     # Dynamic disclaimer display
│       ├── LegalWarningModal.tsx    # Blocking legal warnings
│       ├── TermsAcceptanceModal.tsx # Terms acceptance UI
│       ├── AttorneyVerificationForm.tsx # Bar verification
│       └── ComplianceWrapper.tsx    # Compliance enforcement
├── hooks/                       # Custom React hooks
│   ├── useAuth.ts              # Authentication management
│   ├── useCompliance.ts        # Compliance status tracking
│   ├── useDisclaimers.ts       # Disclaimer management
│   └── useTermsAcceptance.ts   # Terms acceptance handling
├── types/                      # TypeScript type definitions
│   └── legal-compliance.ts    # Comprehensive compliance types
├── utils/                      # Utility functions
│   └── compliance-utils.ts     # Compliance helper functions
├── providers/                  # React context providers
│   └── AuthProvider.tsx        # Authentication context
└── middleware.ts               # Next.js middleware for route protection
```

## 🔒 Compliance Features

### Disclaimer System
- **19 Disclaimer Types**: Comprehensive legal disclaimers for different contexts
- **8 Display Formats**: Modal, banner, inline, tooltip, watermark, etc.
- **Role-Based Display**: Show relevant disclaimers based on user role
- **Context-Aware**: Display disclaimers based on current page/action
- **Acknowledgment Tracking**: Record and audit disclaimer acknowledgments

### Terms Acceptance
- **Forced Acceptance**: Block system access until terms are accepted
- **Document Versioning**: Track acceptance of specific document versions
- **Audit Trail**: Complete record of acceptance with IP and timestamp
- **Multiple Documents**: Support for Terms, Privacy Policy, AUP, etc.
- **Progressive Acceptance**: Handle new terms for existing users

### Attorney Verification
- **Bar Number Verification**: Real-time verification with state bar APIs
- **License Status Checking**: Active, inactive, suspended, retired
- **Disciplinary Status**: Good standing, disciplinary action, etc.
- **Credential Caching**: Cache verification results with expiration
- **Manual Review**: Fallback for complex verification cases

## 🚀 Getting Started

### Prerequisites
```bash
Node.js 18+
npm or yarn
Legal AI System backend running on http://localhost:8000
```

### Installation
```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NODE_ENV=development
```

### Development Commands
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run type checking
npm run typecheck

# Run linting
npm run lint

# Run tests
npm test
```

## 📚 Key Components

### Authentication Pages
- **Login**: `/auth/login` - Secure login with legal disclaimers
- **Register**: `/auth/register` - Registration with terms acceptance
- **Attorney Verification**: `/auth/verify-attorney` - Bar credential verification

### Compliance Components
- **DisclaimerBanner**: Context-aware legal disclaimers
- **LegalWarningModal**: Blocking legal warnings and notices
- **TermsAcceptanceModal**: Comprehensive terms acceptance UI
- **ComplianceWrapper**: Automatic compliance enforcement

### Custom Hooks
- **useAuth**: Authentication state management
- **useCompliance**: Compliance status tracking
- **useDisclaimers**: Dynamic disclaimer management
- **useTermsAcceptance**: Terms acceptance workflow

## 🎨 Design System

### Colors
```css
/* Legal/Professional Colors */
legal: {
  50: '#f8fafc',   /* Light backgrounds */
  600: '#475569',  /* Primary legal color */
  900: '#0f172a',  /* Dark text */
}

/* Compliance Alert Colors */
warning: { 600: '#d97706' }
error: { 600: '#dc2626' }
success: { 600: '#16a34a' }
```

## 🔧 Usage Examples

### Implementing Forced Compliance
```typescript
// Wrap your app with ComplianceWrapper
<ComplianceWrapper>
  <YourAppContent />
</ComplianceWrapper>
```

### Custom Disclaimer Display
```typescript
const { disclaimers } = useDisclaimers(userRole);
const contextDisclaimers = disclaimers.filter(d => 
  d.context.includes('document-analysis')
);
```

### Attorney Verification Flow
```typescript
const { user } = useAuth();
if (user?.role === UserRole.ATTORNEY && !user.isVerified) {
  router.push('/auth/verify-attorney?from=onboarding');
}
```

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

## 🚀 Deployment

### Build Process
```bash
# Create production build
npm run build

# Test production build locally
npm start
```

### Security Features
- CSP headers configured in `next.config.js`
- XSS protection through input sanitization
- CSRF protection with token validation
- Secure cookie settings for authentication

## 📖 Documentation

- [Legal AI System Documentation](../docs/)
- [Professional Responsibility Guide](../docs/professional-responsibility.md)
- [Compliance API Reference](../docs/api-compliance.md)

## 🤝 Contributing

### Code Standards
- TypeScript strict mode enabled
- ESLint + Prettier configuration
- Comprehensive type definitions
- Component documentation required
- Test coverage for compliance features

---

**Legal Notice**: This system is designed to assist legal professionals while maintaining compliance with professional conduct rules and legal industry standards. Users remain fully responsible for professional compliance and legal decisions.

**Version**: 1.0.0 | **License**: Proprietary - Legal AI System