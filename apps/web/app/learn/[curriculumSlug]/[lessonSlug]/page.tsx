import { LearningLessonExperience } from "@/app/components/learning-template/LearningLessonExperience";

export default async function LessonDetailPage({
  params
}: {
  params: Promise<{ curriculumSlug: string; lessonSlug: string }>;
}) {
  const { curriculumSlug, lessonSlug } = await params;

  return <LearningLessonExperience curriculumSlug={curriculumSlug} lessonSlug={lessonSlug} />;
}
