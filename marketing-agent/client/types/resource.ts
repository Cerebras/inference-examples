export interface BaseResource {
  resource_type: string;
  title: string;
  content: string;
}

export interface LinkedInPostMetadata {
  title: string;
  hashtags: string[];
  mentions: string[];
  image_description: string;
}

export interface EmailMetadata {
  subject: string;
  attachment_descriptions: string[];
}

export interface TweetMetadata {
  hashtags: string[];
  mentions: string[];
  hook: string;
}

export type Resource =
  | (BaseResource & {
      resource_type: "LinkedInPost";
      metadata: LinkedInPostMetadata;
    })
  | (BaseResource & { resource_type: "Email"; metadata: EmailMetadata })
  | (BaseResource & {
      resource_type: "Tweet";
      metadata: TweetMetadata;
    });
