"use client";

import { useEffect, useState } from "react";
import { publicTestimonialsApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog";
import {
  Video,
  Play,
  Star,
  X,
  Quote,
} from "lucide-react";

interface PublicTestimonial {
  id: string;
  author_name: string;
  author_title: string | null;
  author_company: string | null;
  author_photo_url: string | null;
  quote: string | null;
  video_url: string | null;
  thumbnail_url: string | null;
  video_duration_seconds: number | null;
  featured: boolean;
}

export default function GalleryPage() {
  const [loading, setLoading] = useState(true);
  const [featured, setFeatured] = useState<PublicTestimonial[]>([]);
  const [testimonials, setTestimonials] = useState<PublicTestimonial[]>([]);
  const [activeVideo, setActiveVideo] = useState<PublicTestimonial | null>(null);

  useEffect(() => {
    loadTestimonials();
  }, []);

  const loadTestimonials = async () => {
    try {
      setLoading(true);
      const data = await publicTestimonialsApi.getGallery();
      setFeatured(data.featured);
      setTestimonials(data.items);
    } catch (error) {
      console.error("Failed to load testimonials:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const TestimonialCard = ({ testimonial, featured = false }: { testimonial: PublicTestimonial; featured?: boolean }) => (
    <Card
      className={`overflow-hidden cursor-pointer transition-all hover:shadow-lg ${
        featured ? "border-2 border-amber-200" : ""
      }`}
      onClick={() => testimonial.video_url && setActiveVideo(testimonial)}
    >
      <CardContent className="p-0">
        {/* Video Thumbnail */}
        <div className={`relative bg-gray-900 ${featured ? "aspect-video" : "aspect-[4/3]"}`}>
          {testimonial.thumbnail_url ? (
            <img
              src={testimonial.thumbnail_url}
              alt={testimonial.author_name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Video className="h-12 w-12 text-gray-600" />
            </div>
          )}

          {/* Play overlay */}
          {testimonial.video_url && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity">
              <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center">
                <Play className="h-8 w-8 text-gray-900 ml-1" />
              </div>
            </div>
          )}

          {/* Duration badge */}
          {testimonial.video_duration_seconds && (
            <span className="absolute bottom-2 right-2 text-xs bg-black/70 text-white px-2 py-0.5 rounded">
              {formatDuration(testimonial.video_duration_seconds)}
            </span>
          )}

          {/* Featured badge */}
          {testimonial.featured && (
            <div className="absolute top-2 left-2 bg-amber-500 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
              <Star className="h-3 w-3 fill-current" />
              Featured
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          {testimonial.quote && (
            <p className="text-gray-600 text-sm mb-3 line-clamp-2 italic">
              "{testimonial.quote}"
            </p>
          )}

          <div className="flex items-center gap-3">
            {testimonial.author_photo_url ? (
              <img
                src={testimonial.author_photo_url}
                alt={testimonial.author_name}
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                <span className="text-violet-600 font-medium">
                  {testimonial.author_name.charAt(0)}
                </span>
              </div>
            )}
            <div className="min-w-0">
              <p className="font-medium text-gray-900 truncate">
                {testimonial.author_name}
              </p>
              {(testimonial.author_title || testimonial.author_company) && (
                <p className="text-sm text-gray-500 truncate">
                  {testimonial.author_title}
                  {testimonial.author_title && testimonial.author_company && " at "}
                  {testimonial.author_company}
                </p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading testimonials...</div>
      </div>
    );
  }

  const allTestimonials = [...featured, ...testimonials];

  if (allTestimonials.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Video className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">No testimonials yet</h2>
          <p className="text-gray-500 mt-2">Check back soon!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto py-16 px-4 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            What Our Clients Say
          </h1>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Hear from the amazing women who have transformed their careers and lives through our coaching programs.
          </p>
        </div>
      </div>

      {/* Featured Testimonials */}
      {featured.length > 0 && (
        <div className="max-w-7xl mx-auto py-12 px-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Star className="h-6 w-6 text-amber-500" />
            Featured Stories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {featured.map((t) => (
              <TestimonialCard key={t.id} testimonial={t} featured />
            ))}
          </div>
        </div>
      )}

      {/* All Testimonials */}
      {testimonials.length > 0 && (
        <div className="max-w-7xl mx-auto py-12 px-4">
          {featured.length > 0 && (
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              More Stories
            </h2>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {testimonials.map((t) => (
              <TestimonialCard key={t.id} testimonial={t} />
            ))}
          </div>
        </div>
      )}

      {/* Video Player Modal */}
      <Dialog open={!!activeVideo} onOpenChange={() => setActiveVideo(null)}>
        <DialogContent className="max-w-4xl p-0 overflow-hidden">
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 z-10 bg-black/50 hover:bg-black/70 text-white"
            onClick={() => setActiveVideo(null)}
          >
            <X className="h-5 w-5" />
          </Button>

          {activeVideo && (
            <div>
              <div className="aspect-video bg-black">
                <video
                  src={activeVideo.video_url || ""}
                  controls
                  autoPlay
                  className="w-full h-full"
                />
              </div>
              <div className="p-6 bg-white">
                {activeVideo.quote && (
                  <div className="flex gap-3 mb-4">
                    <Quote className="h-6 w-6 text-violet-400 flex-shrink-0" />
                    <p className="text-gray-700 italic">{activeVideo.quote}</p>
                  </div>
                )}
                <div className="flex items-center gap-4">
                  {activeVideo.author_photo_url ? (
                    <img
                      src={activeVideo.author_photo_url}
                      alt={activeVideo.author_name}
                      className="w-14 h-14 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-14 h-14 rounded-full bg-violet-100 flex items-center justify-center">
                      <span className="text-violet-600 font-medium text-xl">
                        {activeVideo.author_name.charAt(0)}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="font-semibold text-lg text-gray-900">
                      {activeVideo.author_name}
                    </p>
                    {(activeVideo.author_title || activeVideo.author_company) && (
                      <p className="text-gray-500">
                        {activeVideo.author_title}
                        {activeVideo.author_title && activeVideo.author_company && " at "}
                        {activeVideo.author_company}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
