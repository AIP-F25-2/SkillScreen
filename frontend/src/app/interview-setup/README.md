# Interview Setup Page

## Overview
The Interview Setup page allows candidates to test their camera and microphone before joining an interview. This page works for both authenticated users and guest users.

## Features

### 🎥 Camera Testing
- Live video preview
- Camera device selection
- Real-time video feed display

### 🎤 Microphone Testing
- Audio level visualization
- Microphone device selection
- Real-time audio monitoring

### 👤 User Support
- **Authenticated Users**: Name is automatically pulled from user profile
- **Guest Users**: Can enter their name manually

### ✅ Permission Management
- Visual permission status indicators
- Easy-to-use permission request flow
- Clear feedback on granted/denied permissions

## Usage

### Direct Access
Navigate to `/interview-setup` in your browser.

### With Query Parameters
You can pass optional query parameters:
- `id`: Interview ID (e.g., `/interview-setup?id=interview-456`)

### Navigation Flow
1. **Setup Page** (`/interview-setup`)
   - Test camera and microphone
   - Select devices
   - Enter name (for guests)
   
2. **Join Interview** (Button click)
   - Redirects to `/interview` with query parameters
   - Passes `id` (interview ID) and `name` (participant name)

## URL Structure

### Interview Setup
```
/interview-setup?id=interview-123
```

### After Setup (redirects to)
```
/interview?id=interview-123&name=John%20Doe
```

## Technical Details

### State Management
- Uses local state for media device management
- Integrates with `AuthContext` for authenticated users
- Manages media streams and audio context

### Media Handling
- **Video**: Uses `getUserMedia` API with video constraints
- **Audio**: Uses Web Audio API for level monitoring
- **Cleanup**: Properly stops all tracks on unmount

### Browser Permissions
The page requests:
- Camera access (`video`)
- Microphone access (`audio`)

### Device Selection
Supports selecting from:
- Multiple camera devices
- Multiple microphone devices

## Troubleshooting

### Camera Not Working
1. Check browser permissions
2. Ensure camera is not in use by another application
3. Try selecting a different camera from the dropdown

### Microphone Not Working
1. Check browser permissions
2. Check system microphone settings
3. Try selecting a different microphone from the dropdown

### No Devices Available
- Ensure devices are properly connected
- Refresh the page after connecting devices
- Check browser compatibility

## Browser Support
Requires browsers with:
- `getUserMedia` API support
- Web Audio API support
- Modern ES6+ JavaScript features

Recommended browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Integration

### From Candidate Dashboard
```tsx
import { useRouter } from 'next/navigation';

const router = useRouter();
router.push('/interview-setup?id=interview-123');
```

### Programmatic Navigation
```typescript
// With Next.js Link
<Link href="/interview-setup?id=interview-456">
  Setup Interview
</Link>

// With router
router.push('/interview-setup');
```

## Future Enhancements
- [ ] Network speed test
- [ ] Browser compatibility check
- [ ] Echo cancellation test
- [ ] Background blur/virtual background
- [ ] Recording test sample
- [ ] System check report download


