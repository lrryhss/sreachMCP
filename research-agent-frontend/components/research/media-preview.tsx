'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Play, ExternalLink, X, Maximize2 } from 'lucide-react';
import { Dialog, DialogContent, DialogClose } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import type { MediaItem } from '@/lib/types';

interface MediaPreviewProps {
  media: MediaItem;
  className?: string;
}

export function MediaPreview({ media, className = '' }: MediaPreviewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Detect media type from URL if not specified
  const getMediaType = (url: string): MediaItem['type'] => {
    if (media.type) return media.type;

    if (url.includes('youtube.com') || url.includes('youtu.be')) {
      return 'youtube';
    } else if (url.includes('tiktok.com')) {
      return 'tiktok';
    } else if (url.match(/\.(mp4|webm|ogg)$/i)) {
      return 'video';
    } else {
      return 'image';
    }
  };

  const mediaType = getMediaType(media.url);

  // Extract YouTube video ID
  const getYoutubeId = (url: string): string | null => {
    const match = url.match(
      /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/
    );
    return match ? match[1] : null;
  };

  // Extract TikTok video ID
  const getTikTokId = (url: string): string | null => {
    const match = url.match(/\/video\/(\d+)/);
    return match ? match[1] : null;
  };

  const renderMedia = () => {
    switch (mediaType) {
      case 'youtube': {
        const videoId = getYoutubeId(media.url);
        if (!videoId) return null;

        return (
          <div className="relative w-full h-full">
            <iframe
              src={`https://www.youtube.com/embed/${videoId}`}
              title={media.title || 'YouTube video'}
              className="absolute inset-0 w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
            <div className="absolute top-2 right-2">
              <Button
                size="icon"
                variant="secondary"
                onClick={() => setIsFullscreen(true)}
                className="bg-black/50 hover:bg-black/70 text-white"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        );
      }

      case 'tiktok': {
        // TikTok requires special embedding
        return (
          <div className="relative w-full h-full flex items-center justify-center bg-black">
            <div className="text-center text-white">
              <Play className="h-12 w-12 mx-auto mb-2" />
              <p className="text-sm">TikTok Video</p>
              <a
                href={media.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-xs hover:underline"
              >
                Watch on TikTok
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        );
      }

      case 'video': {
        return (
          <video
            controls
            className="w-full h-full object-cover"
            poster={media.thumbnail}
          >
            <source src={media.url} />
            Your browser does not support the video tag.
          </video>
        );
      }

      case 'image':
      default: {
        if (imageError) {
          return (
            <div className="w-full h-full flex items-center justify-center bg-muted">
              <p className="text-sm text-muted-foreground">Failed to load image</p>
            </div>
          );
        }

        return (
          <div className="relative w-full h-full">
            <img
              src={media.url}
              alt={media.title || 'Image'}
              className="w-full h-full object-cover cursor-pointer"
              onClick={() => setIsFullscreen(true)}
              onError={() => setImageError(true)}
            />
            <div className="absolute top-2 right-2">
              <Button
                size="icon"
                variant="secondary"
                onClick={() => setIsFullscreen(true)}
                className="bg-black/50 hover:bg-black/70 text-white"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        );
      }
    }
  };

  return (
    <>
      <div className={`relative overflow-hidden rounded-lg ${className}`}>
        {renderMedia()}
        {media.title && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
            <p className="text-white text-sm truncate">{media.title}</p>
          </div>
        )}
      </div>

      {/* Fullscreen Dialog for images */}
      {mediaType === 'image' && (
        <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
          <DialogContent className="max-w-screen-lg p-0">
            <DialogClose className="absolute right-4 top-4 z-50">
              <Button size="icon" variant="secondary">
                <X className="h-4 w-4" />
              </Button>
            </DialogClose>
            <img
              src={media.url}
              alt={media.title || 'Image'}
              className="w-full h-auto max-h-[90vh] object-contain"
            />
            {media.description && (
              <div className="p-4 border-t">
                <p className="text-sm text-muted-foreground">{media.description}</p>
              </div>
            )}
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}

interface MediaGalleryProps {
  media: MediaItem[];
  className?: string;
}

export function MediaGallery({ media, className = '' }: MediaGalleryProps) {
  if (!media || media.length === 0) return null;

  return (
    <div className={`grid grid-cols-2 md:grid-cols-3 gap-3 ${className}`}>
      {media.map((item, index) => (
        <MediaPreview
          key={index}
          media={item}
          className="aspect-video"
        />
      ))}
    </div>
  );
}