"""
Pixel Art Transformer - Custom Exceptions
==========================================
Structured error handling for the application.
"""


class PixelArtError(Exception):
    """Base exception for all Pixel Art Transformer errors."""
    
    def __init__(self, message: str, details: str | None = None):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message.
            details: Optional technical details for debugging.
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class InvalidImageError(PixelArtError):
    """Raised when an image cannot be loaded or processed."""
    
    def __init__(self, path: str, reason: str = "Unknown error"):
        """
        Initialize the exception.
        
        Args:
            path: Path to the problematic image file.
            reason: Why the image is invalid.
        """
        self.path = path
        super().__init__(
            message=f"Cannot process image: {reason}",
            details=f"File: {path}"
        )


class GridDetectionError(PixelArtError):
    """Raised when grid detection fails."""
    
    def __init__(self, image_size: tuple[int, int], reason: str = "No pattern detected"):
        """
        Initialize the exception.
        
        Args:
            image_size: Size of the image (width, height).
            reason: Why detection failed.
        """
        self.image_size = image_size
        super().__init__(
            message=f"Grid detection failed: {reason}",
            details=f"Image size: {image_size[0]}x{image_size[1]}"
        )


class ProcessingError(PixelArtError):
    """Raised when image processing fails."""
    
    def __init__(self, operation: str, reason: str):
        """
        Initialize the exception.
        
        Args:
            operation: The operation that failed.
            reason: Why it failed.
        """
        self.operation = operation
        super().__init__(
            message=f"Processing failed during {operation}",
            details=reason
        )


class RegionError(PixelArtError):
    """Raised when region operations fail."""
    
    def __init__(self, region_coords: tuple[int, int, int, int], reason: str):
        """
        Initialize the exception.
        
        Args:
            region_coords: The region coordinates (x1, y1, x2, y2).
            reason: Why the operation failed.
        """
        self.region_coords = region_coords
        super().__init__(
            message=f"Region operation failed: {reason}",
            details=f"Region: {region_coords}"
        )
