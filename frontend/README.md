# InterviewAI Platform

A modern, responsive landing page for an AI-powered interview platform built with Next.js and Tailwind CSS.

## Features

- **Modern Design**: Clean, professional interface inspired by the Codavra design
- **Breathing Animation**: Subtle black circle background with breathing animation effect
- **Custom Color Palette**: 
  - Primary: `#1B3C53` (Dark Blue-Gray)
  - Secondary: `#234C6A` (Medium Blue-Gray) 
  - Accent: `#456882` (Light Blue-Gray)
  - Text: `#FFFFFF` (White)
- **Responsive Layout**: Mobile-first design that works on all devices
- **Interactive Components**: Smooth hover effects and transitions
- **Accessibility**: Proper ARIA labels and keyboard navigation

## Tech Stack

- **Next.js 15.5.3** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS v4** - Utility-first CSS framework
- **React 19** - Latest React features

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Run the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser** and navigate to `http://localhost:3000`

## Project Structure

```
src/
├── app/
│   ├── globals.css          # Global styles and breathing animation
│   ├── layout.tsx           # Root layout component
│   └── page.tsx             # Main landing page
└── components/
    ├── Header.tsx           # Navigation header with mobile menu
    └── Hero.tsx             # Main hero section with CTA
```

## Customization

### Colors
The color palette is defined in `tailwind.config.ts` and can be easily modified:

```typescript
colors: {
  primary: {
    50: '#FFFFFF',   // White
    100: '#456882',  // Light Blue-Gray
    200: '#234C6A',  // Medium Blue-Gray
    300: '#1B3C53',  // Dark Blue-Gray
  }
}
```

### Animation
The breathing circle animation is defined in `globals.css` and can be adjusted:

```css
.breathing-circle {
  animation: breathe 4s ease-in-out infinite;
}
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is created for demonstration purposes.