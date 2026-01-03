/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ['class'],
    content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Design System - Primary Navy
        navy: {
          '50': '#f8fafc',
          '100': '#e2e8f0',
          '200': '#cbd5e1',
          '300': '#94a3b8',
          '400': '#64748b',
          '500': '#475569',
          '600': '#334155',
          '700': '#1e293b',
          '800': '#1a365d',  // Primary - Deep navy
          '900': '#0f172a',
          DEFAULT: '#1a365d'
        },
        // Design System - Accent Teal
        teal: {
          '50': '#f0fdfa',
          '100': '#ccfbf1',
          '200': '#99f6e4',
          '300': '#5eead4',
          '400': '#2dd4bf',
          '500': '#14b8a6',
          '600': '#0d9488',  // Primary accent
          '700': '#0f766e',
          '800': '#115e59',
          '900': '#134e4a',
          DEFAULT: '#0d9488'
        },
        // Design System - Gold Accent
        gold: {
          '50': '#fffbeb',
          '100': '#fef3c7',
          '200': '#fde68a',
          '300': '#fcd34d',
          '400': '#fbbf24',
          '500': '#f59e0b',
          '600': '#d97706',  // Accent gold
          '700': '#b45309',
          '800': '#92400e',
          '900': '#78350f',
          DEFAULT: '#d97706'
        },
        // Neutral grays (design system)
        slate: {
          '50': '#f8fafc',   // Light backgrounds
          '100': '#f1f5f9',
          '200': '#e2e8f0',  // Borders
          '300': '#cbd5e1',
          '400': '#94a3b8',
          '500': '#64748b',  // Secondary text
          '600': '#475569',
          '700': '#334155',
          '800': '#1e293b',
          '900': '#0f172a',
        },
        primary: {
          '50': '#f8fafc',
          '100': '#e2e8f0',
          '200': '#cbd5e1',
          '300': '#94a3b8',
          '400': '#64748b',
          '500': '#475569',
          '600': '#334155',
          '700': '#1e293b',
          '800': '#1a365d',
          '900': '#0f172a',
          DEFAULT: '#1a365d',
          foreground: '#ffffff'
        },
        gray: {
          '50': '#f9fafb',
          '100': '#f3f4f6',
          '200': '#e5e7eb',
          '300': '#d1d5db',
          '400': '#9ca3af',
          '500': '#6b7280',
          '600': '#4b5563',
          '700': '#374151',
          '800': '#1f2937',
          '900': '#111827'
        },
        // Warning - Amber
        warning: {
          '50': '#fffbeb',
          '100': '#fef3c7',
          '200': '#fde68a',
          '300': '#fcd34d',
          '400': '#fbbf24',
          '500': '#f59e0b',  // Primary warning
          '600': '#d97706',
          '700': '#b45309',
          '800': '#92400e',
          '900': '#78350f',
          DEFAULT: '#f59e0b'
        },
        // Error - Soft red
        error: {
          '50': '#fef2f2',
          '100': '#fee2e2',
          '200': '#fecaca',
          '300': '#fca5a5',
          '400': '#f87171',
          '500': '#ef4444',
          '600': '#dc2626',  // Primary error
          '700': '#b91c1c',
          '800': '#991b1b',
          '900': '#7f1d1d',
          DEFAULT: '#dc2626'
        },
        // Success - Teal
        success: {
          '50': '#f0fdfa',
          '100': '#ccfbf1',
          '200': '#99f6e4',
          '300': '#5eead4',
          '400': '#2dd4bf',
          '500': '#14b8a6',
          '600': '#0d9488',  // Primary success
          '700': '#0f766e',
          '800': '#115e59',
          '900': '#134e4a',
          DEFAULT: '#0d9488'
        },
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          'DM Sans',
          'system-ui',
          'sans-serif'
        ],
        serif: [
          'Georgia',
          'Times New Roman',
          'serif'
        ],
        mono: [
          'JetBrains Mono',
          'Monaco',
          'monospace'
        ]
      },
      fontSize: {
        // Design system typography
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.6' }],
        'lg': ['1.125rem', { lineHeight: '1.6' }],
        'xl': ['1.25rem', { lineHeight: '1.5' }],  // H3
        '2xl': ['1.5rem', { lineHeight: '1.4' }],   // H2
        '3xl': ['1.875rem', { lineHeight: '1.3' }],
        '4xl': ['2rem', { lineHeight: '1.2' }],     // H1
        '5xl': ['2.5rem', { lineHeight: '1.2' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem'
      },
      maxWidth: {
        'content': '1200px',  // Design system max content width
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.2s ease-out',
        'slide-in-right': 'slide-in-right 0.2s ease-out',
        'bounce-subtle': 'bounce-subtle 2s infinite'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        'bounce-subtle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-2px)' }
        }
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
      borderRadius: {
        'lg': '0.5rem',  // 8px
        'md': '0.375rem',
        'sm': '0.25rem',
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      transitionDuration: {
        'DEFAULT': '200ms',
      },
      transitionTimingFunction: {
        'DEFAULT': 'ease',
      }
    }
  },
  plugins: [
    require('@headlessui/tailwindcss'),
    require("tailwindcss-animate")
  ],
}
