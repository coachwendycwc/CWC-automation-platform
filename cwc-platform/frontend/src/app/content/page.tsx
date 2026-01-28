"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import { contentApi, Content } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import Link from "next/link";
import {
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  FileText,
  Video,
  Link as LinkIcon,
  File,
  Calendar,
  User,
  Building,
  FolderOpen,
  Eye,
  EyeOff,
} from "lucide-react";
import { toast } from "sonner";

const CONTENT_TYPE_ICONS: Record<string, React.ElementType> = {
  file: File,
  document: FileText,
  video: Video,
  link: LinkIcon,
};

const CONTENT_TYPE_COLORS: Record<string, string> = {
  file: "bg-blue-100 text-blue-600",
  document: "bg-purple-100 text-purple-600",
  video: "bg-red-100 text-red-600",
  link: "bg-green-100 text-green-600",
};

export default function ContentPage() {
  const { token } = useAuth();
  const [content, setContent] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [contentType, setContentType] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [categories, setCategories] = useState<string[]>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadContent();
    loadCategories();
  }, [token, page, search, contentType, category]);

  const loadContent = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const result = await contentApi.list(token, {
        page,
        size: 20,
        search: search || undefined,
        content_type: contentType || undefined,
        category: category || undefined,
      });
      setContent(result.items);
      setTotal(result.total);
    } catch (error) {
      console.error("Failed to load content:", error);
      toast.error("Failed to load content");
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    if (!token) return;
    try {
      const result = await contentApi.getCategories(token);
      setCategories(result.categories);
    } catch (error) {
      console.error("Failed to load categories:", error);
    }
  };

  const handleDelete = async () => {
    if (!token || !deleteId) return;
    try {
      await contentApi.delete(token, deleteId);
      toast.success("Content deleted");
      loadContent();
    } catch (error) {
      console.error("Failed to delete content:", error);
      toast.error("Failed to delete content");
    } finally {
      setDeleteId(null);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "-";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <Shell>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Content Library</h1>
          <p className="text-gray-500">
            Manage files, videos, and links for your clients
          </p>
        </div>
        <Link href="/content/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Content
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search content..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10"
                />
              </div>
            </div>
            <Select
              value={contentType}
              onValueChange={(value) => {
                setContentType(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                <SelectItem value="file">File</SelectItem>
                <SelectItem value="document">Document</SelectItem>
                <SelectItem value="video">Video</SelectItem>
                <SelectItem value="link">Link</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={category}
              onValueChange={(value) => {
                setCategory(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Content Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Content</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Release Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : content.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <FolderOpen className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-500">No content found</p>
                  </TableCell>
                </TableRow>
              ) : (
                content.map((item) => {
                  const Icon = CONTENT_TYPE_ICONS[item.content_type] || File;
                  const colorClass =
                    CONTENT_TYPE_COLORS[item.content_type] ||
                    "bg-gray-100 text-gray-600";

                  return (
                    <TableRow key={item.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${colorClass}`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div>
                            <p className="font-medium">{item.title}</p>
                            {item.description && (
                              <p className="text-sm text-gray-500 line-clamp-1">
                                {item.description}
                              </p>
                            )}
                            {item.file_size && (
                              <p className="text-xs text-gray-400">
                                {formatFileSize(item.file_size)}
                              </p>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {item.content_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {item.contact_name ? (
                          <div className="flex items-center gap-1.5 text-sm">
                            <User className="h-3.5 w-3.5 text-gray-400" />
                            {item.contact_name}
                          </div>
                        ) : item.organization_name ? (
                          <div className="flex items-center gap-1.5 text-sm">
                            <Building className="h-3.5 w-3.5 text-gray-400" />
                            {item.organization_name}
                          </div>
                        ) : item.project_name ? (
                          <div className="flex items-center gap-1.5 text-sm">
                            <FolderOpen className="h-3.5 w-3.5 text-gray-400" />
                            {item.project_name}
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm">
                            All clients
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.category ? (
                          <Badge variant="secondary">{item.category}</Badge>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.release_date ? (
                          <div className="flex items-center gap-1.5 text-sm">
                            <Calendar className="h-3.5 w-3.5 text-gray-400" />
                            {formatDate(item.release_date)}
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm">
                            Immediate
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.is_active ? (
                          item.is_released ? (
                            <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                              <Eye className="h-3 w-3 mr-1" />
                              Live
                            </Badge>
                          ) : (
                            <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">
                              <Calendar className="h-3 w-3 mr-1" />
                              Scheduled
                            </Badge>
                          )
                        ) : (
                          <Badge variant="outline" className="text-gray-500">
                            <EyeOff className="h-3 w-3 mr-1" />
                            Hidden
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link href={`/content/${item.id}`}>
                                <Pencil className="h-4 w-4 mr-2" />
                                Edit
                              </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => setDeleteId(item.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of{" "}
            {total} items
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Content</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this content? This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
    </Shell>
  );
}
