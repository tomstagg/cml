import type { Metadata } from "next";
import { ReviewForm } from "@/components/ReviewForm";

export const metadata: Metadata = {
  title: "Leave a Review",
  description: "Share your experience with your solicitor.",
};

export default function ReviewPage({ params }: { params: { token: string } }) {
  return <ReviewForm token={params.token} />;
}
