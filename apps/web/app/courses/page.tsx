import { Suspense } from "react";

import { CourseCatalog } from "@/app/components/courses/CourseCatalog";

export default function CoursesPage() {
  return (
    <Suspense>
      <CourseCatalog />
    </Suspense>
  );
}
