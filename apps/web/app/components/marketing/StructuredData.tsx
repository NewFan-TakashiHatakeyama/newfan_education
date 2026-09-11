import { journeyFaqs, journeySeo } from "./journeyContent";
export function StructuredData() {
 const schema = {"@context":"https://schema.org","@graph":[{"@type":"FAQPage",mainEntity:journeyFaqs.map(f=>({"@type":"Question",name:f.q,acceptedAnswer:{"@type":"Answer",text:f.a}}))},{"@type":"SoftwareApplication",name:"AI Field Ready Enterprise",applicationCategory:"BusinessApplication",operatingSystem:"Web",description:journeySeo.description}]};
 return <script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(schema).replace(/</g,"\\u003c")}}/>;
}
