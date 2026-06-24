import { CourseDetailView } from "@/app/components/courses/CourseDetailView";

export default async function CourseDetailPage({
  params
}: {
  params: Promise<{ courseSlug: string }>;
}) {
  const { courseSlug } = await params;

  return <CourseDetailView courseSlug={courseSlug} />;
}
