import { LearningLessonExperience } from "@/app/components/learning-template/LearningLessonExperience";
import {
  listCourseLessons,
  loadEnterpriseCurriculumBySlug
} from "@/lib/curriculumMdx.server";

export default async function LessonDetailPage({
  params
}: {
  params: Promise<{ curriculumSlug: string; lessonSlug: string }>;
}) {
  const { curriculumSlug, lessonSlug } = await params;

  // Course-aware mode: a directory of per-lesson MDX under the course slug.
  const lessons = await listCourseLessons(curriculumSlug);
  if (lessons.length > 0) {
    const current = lessons.find((lesson) => lesson.slug === lessonSlug) ?? lessons[0];
    return (
      <LearningLessonExperience
        courseSlug={curriculumSlug}
        lessonSlug={current.slug}
        lessons={lessons.map((lesson) => ({
          slug: lesson.slug,
          title: lesson.title,
          kind: lesson.kind
        }))}
        title={current.title}
        body={current.body}
        kind={current.kind}
        exerciseId={current.exerciseId}
        skillTags={current.skillTags}
        estimatedMinutes={current.estimatedMinutes}
        section={current.section}
      />
    );
  }

  // Enterprise single-MDX fallback (12-week curriculum).
  const curriculumModule = await loadEnterpriseCurriculumBySlug(curriculumSlug);
  return (
    <LearningLessonExperience
      courseSlug={curriculumSlug}
      lessonSlug={lessonSlug}
      lessons={[]}
      title={curriculumModule?.title ?? "Enterprise カリキュラム"}
      body={curriculumModule?.body ?? null}
      kind="reading"
      skillTags={curriculumModule?.skillTags ?? []}
      estimatedMinutes={curriculumModule?.estimatedMinutes}
      week={curriculumModule?.week}
      phase={curriculumModule?.phase}
      deliverable={curriculumModule?.deliverable}
    />
  );
}
