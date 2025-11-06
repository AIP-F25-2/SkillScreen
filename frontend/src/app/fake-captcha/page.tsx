'use client';

import { useState, useEffect, useRef } from 'react';
import { CheckCircle, RefreshCw, Move } from 'lucide-react';

const GRID_SIZE = 3; // 3x3 grid = 9 pieces
const TOTAL_PIECES = GRID_SIZE * GRID_SIZE;

interface PuzzlePiece {
  id: number;
  correctPosition: number;
  currentPosition: number;
}

export default function FakeCaptchaPage() {
  const [pieces, setPieces] = useState<PuzzlePiece[]>([]);
  const [draggedPiece, setDraggedPiece] = useState<number | null>(null);
  const [isVerified, setIsVerified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [moves, setMoves] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize puzzle pieces
  useEffect(() => {
    initializePuzzle();
  }, []);

  const initializePuzzle = () => {
    // Create pieces with correct positions
    const initialPieces: PuzzlePiece[] = Array.from({ length: TOTAL_PIECES }, (_, i) => ({
      id: i,
      correctPosition: i,
      currentPosition: i,
    }));

    // Shuffle pieces (but keep one piece in correct position for easier solving)
    const shuffled = [...initialPieces];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i].currentPosition, shuffled[j].currentPosition] = 
        [shuffled[j].currentPosition, shuffled[i].currentPosition];
    }

    setPieces(shuffled);
    setIsVerified(false);
    setMoves(0);
  };

  const handleDragStart = (pieceId: number) => {
    setDraggedPiece(pieceId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (targetPosition: number) => {
    if (draggedPiece === null) return;

    const newPieces = [...pieces];
    const draggedPieceIndex = newPieces.findIndex(p => p.id === draggedPiece);
    const targetPieceIndex = newPieces.findIndex(p => p.currentPosition === targetPosition);

    if (draggedPieceIndex !== -1 && targetPieceIndex !== -1) {
      // Swap positions
      const temp = newPieces[draggedPieceIndex].currentPosition;
      newPieces[draggedPieceIndex].currentPosition = newPieces[targetPieceIndex].currentPosition;
      newPieces[targetPieceIndex].currentPosition = temp;

      setPieces(newPieces);
      setMoves(prev => prev + 1);
      checkIfSolved(newPieces);
    }

    setDraggedPiece(null);
  };

  const checkIfSolved = (currentPieces: PuzzlePiece[]) => {
    const isSolved = currentPieces.every(
      piece => piece.currentPosition === piece.correctPosition
    );

    if (isSolved) {
      setIsLoading(true);
      setTimeout(() => {
        setIsLoading(false);
        setIsVerified(true);
      }, 1000);
    }
  };

  const getPieceStyle = (piece: PuzzlePiece) => {
    const row = Math.floor(piece.correctPosition / GRID_SIZE);
    const col = piece.correctPosition % GRID_SIZE;
    const xPercent = (col / GRID_SIZE) * 100;
    const yPercent = (row / GRID_SIZE) * 100;

    return {
      backgroundImage: 'url(/images/image.png)',
      backgroundSize: `${GRID_SIZE * 100}%`,
      backgroundPosition: `${xPercent}% ${yPercent}%`,
    };
  };

  const getCurrentGridPosition = (position: number) => {
    const row = Math.floor(position / GRID_SIZE);
    const col = position % GRID_SIZE;
    return { row, col };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-2xl w-full">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Verify you're human</h1>
          <p className="text-sm text-gray-600">Complete the puzzle to continue</p>
        </div>

        {/* Puzzle Section */}
        <div className="mb-6">
          <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-6 mb-4">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-gray-700">
                Drag the pieces to complete the image
              </p>
              <div className="flex items-center space-x-4">
                <span className="text-xs text-gray-500">Moves: {moves}</span>
                {isVerified && (
                  <div className="flex items-center space-x-1 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-xs font-medium">Solved!</span>
                  </div>
                )}
              </div>
            </div>

            {/* Puzzle Grid */}
            <div
              ref={containerRef}
              className="grid grid-cols-3 gap-2 mx-auto"
              style={{ width: '400px', height: '400px' }}
            >
              {Array.from({ length: TOTAL_PIECES }).map((_, index) => {
                const piece = pieces.find(p => p.currentPosition === index);
                if (!piece) return null;

                const isCorrect = piece.currentPosition === piece.correctPosition;
                const isDragging = draggedPiece === piece.id;

                return (
                  <div
                    key={piece.id}
                    draggable
                    onDragStart={() => handleDragStart(piece.id)}
                    onDragOver={handleDragOver}
                    onDrop={() => handleDrop(index)}
                    className={`
                      relative border-2 rounded transition-all cursor-move
                      ${isCorrect && isVerified ? 'border-green-500' : 'border-gray-400'}
                      ${isDragging ? 'opacity-50 scale-95' : 'hover:border-blue-500 hover:shadow-md'}
                      ${!isVerified ? 'active:cursor-grabbing' : 'cursor-default'}
                    `}
                    style={{
                      ...getPieceStyle(piece),
                      width: '100%',
                      height: '100%',
                      minHeight: '130px',
                    }}
                  >
                    {!isVerified && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/5 opacity-0 hover:opacity-100 transition-opacity">
                        <Move className="w-6 h-6 text-gray-600" />
                      </div>
                    )}
                    {isCorrect && isVerified && (
                      <div className="absolute top-1 right-1">
                        <CheckCircle className="w-5 h-5 text-green-600 bg-white rounded-full" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Instructions */}
            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                Click and drag pieces to rearrange them
              </p>
            </div>
          </div>

          {/* Checkbox */}
          <div className="flex items-start space-x-3 mb-4">
            <div className="flex items-center h-5">
              <input
                id="captcha-checkbox"
                type="checkbox"
                checked={isVerified}
                disabled
                className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 cursor-not-allowed"
              />
            </div>
            <label htmlFor="captcha-checkbox" className="text-sm text-gray-700">
              I'm not a robot
            </label>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="mb-4 flex items-center justify-center space-x-2 text-blue-600">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span className="text-sm">Verifying...</span>
            </div>
          )}

          {/* Success State */}
          {isVerified && !isLoading && (
            <div className="mb-4 flex items-center justify-center space-x-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm font-medium">Verification successful!</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={initializePuzzle}
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors flex items-center justify-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reset Puzzle</span>
          </button>
          <button
            disabled={!isVerified}
            className={`flex-1 px-4 py-2 text-sm font-medium text-white rounded-md transition-colors ${
              isVerified
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-300 cursor-not-allowed'
            }`}
          >
            Continue
          </button>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Protected by reCAPTCHA • Privacy • Terms
          </p>
        </div>
      </div>
    </div>
  );
}
