import { useState, type ReactNode } from "react";
import { Link } from "@/lib/router";
import { PageTitle } from "@/components/Layout";
import { ChevronDown } from "@/components/Icons";
import { cn } from "@/utils/cn";

/** A collapsed disclosure used for the "Special Notices" section. */
function Disclosure({
  id,
  label,
  children,
}: {
  id: string;
  label: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div id={id} className="mb-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 bg-[#e6e6e6] px-3 py-2 text-left text-[14px] text-[#333] hover:bg-[#dcdcdc]"
      >
        <span>{label}</span>
        <ChevronDown
          size={13}
          className={cn("shrink-0 text-[#666] transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div className="border-x border-b border-[#ddd] px-3 py-3 text-[13.5px] leading-relaxed text-[#333]">
          {children}
        </div>
      )}
    </div>
  );
}

export function PrivacyStatementPage() {
  return (
    <>
      <PageTitle>Corravale Privacy Statement</PageTitle>
      <section className="bg-[#f4f4f4] py-10">
        <div className="mx-auto max-w-[820px] px-5 text-[14px] leading-relaxed text-[#333]">
          <p className="mb-4">Last Revision Date — March 14, 2023</p>
          <p className="mb-4">
            Corravale University (CU) recognizes and values the privacy of its community members and
            guests. This commitment is reflected in Trustees' Bylaw Sec. 14.07, Privacy and Access to
            Information, which states in part:
          </p>
          <p className="mb-6">
            “In gathering, using, and disclosing information about the individuals connected with the
            university, the university will work to safeguard personal privacy, to use such information
            solely for the purpose for which it was gathered, and to make individuals aware of the
            personal information about them that is being gathered, used, or disclosed.”
          </p>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Overview</h4>
          <p className="mb-3">In principle, Corravale strives to:</p>
          <ul className="mb-6 list-disc space-y-2 pl-6">
            <li>Gather, retain, and use only the minimum amount of personal information required for its legitimate institutional purposes, and to satisfy the legal obligations that apply to it.</li>
            <li>Make every reasonable effort to keep the personal information we maintain accurate and current.</li>
            <li>Restrict access to the personal information we hold so that only those with a legitimate, clearly defined need are able to view it.</li>
            <li>Safeguard personal information with suitable physical and technical security controls matched to the sensitivity of the personal data we keep.</li>
            <li>Keep our students, faculty, employees, suppliers, partners, and others informed about how personal information is used across our day-to-day operations.</li>
            <li>Offer opportunities to control your own personal information, as permitted under applicable United States and other laws.</li>
            <li>Embed privacy principles into the design of every project or activity we undertake that relies on the use of personal data.</li>
          </ul>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Scope</h4>
          <p className="mb-3">
            The Corravale Privacy Statement applies broadly to activities carried out by Corravale that
            involve the collection and processing of personal information. It is intended to give you a
            wide-ranging overview of these activities and of the way we approach the protection of your
            privacy.
          </p>
          <p className="mb-6">
            Corravale is a large institution, and it is challenging to present a complete picture of all
            the personal information we gather and use across the organization. You can find more
            specific details in the individual privacy notices published by the schools, departments,
            units, or groups with which you interact.
          </p>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Categories of Personal Information We Collect and Use</h4>
          <p className="mb-3">
            We consider personal information to be any information that relates to an identified or
            identifiable individual person.
          </p>
          <p className="mb-3">
            In general, at an institutional level we collect and make use of the following categories of
            information:
          </p>
          <ul className="mb-6 list-disc space-y-2 pl-6">
            <li><strong>Prospective students</strong> : personal and family details tied to the application and financial aid process, including supporting documentation, identification, and contact information; this may include data relating to ethnic origin, where the prospective student chooses to disclose such data.</li>
            <li><strong>Students</strong> : the details submitted while a prospective student, information about their academic record, their academic performance, and video images captured on campus.</li>
            <li><strong>Faculty and staff</strong> : identification, contact information, biographic details, information related to compensation, to benefits, to family members, and information about their performance at work.</li>
            <li><strong>Visiting scholars and exchange students</strong> : identification, contact information, biographic details, and possibly information related to health.</li>
            <li><strong>Subjects of our research projects</strong> : as required, identification and contact information, together with all of the information that is produced and observed in relation to the subject over the course of the research project.</li>
            <li><strong>Alumni</strong> : identification and contact information, along with donor and giving history.</li>
            <li><strong>Website visitors</strong> : the internet domain from which a visitor reaches the website, the IP address assigned to the visitor's computer, the type of browser in use, and the date and time of the visit.</li>
            <li><strong>Patients of Corravale Health</strong> : identification and contact information, along with data related to health and billing.</li>
          </ul>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">How We Use Personal Information</h4>
          <p className="mb-3">
            We use your personal information only for legitimate and clearly defined purposes and to
            support the many operations that keep the University running.
          </p>
          <p className="mb-3">In general, we make use of personal information in the following ways:</p>
          <ul className="mb-6 list-disc space-y-2 pl-6">
            <li>To facilitate admission and to deliver higher education services to our undergraduate and graduate students and to prospective students.</li>
            <li>To administer the employment of our faculty members and staff.</li>
            <li>To support campus visits for our visiting scholars and exchange students each term.</li>
            <li>To deliver course materials, encourage engagement, and track attendance and completion for the subscribers of our online courses.</li>
            <li>To manage the attendance of individuals who register for conferences, symposia, and other events.</li>
            <li>To keep our alumni connected to the community.</li>
            <li>For the purpose of delivering healthcare services to our patients.</li>
            <li>To enable the participation of individuals who take part in our research projects.</li>
            <li>To support website performance and improve the experience of visitors to our website.</li>
            <li>Video images captured by our video security system to protect the physical safety of our community members and to safeguard our property.</li>
          </ul>
          <p className="mb-6">
            From time to time we may process other personal information for various legitimate and
            specific purposes. Whenever these situations arise, we will make every effort to inform you.
          </p>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Who Has Access to Your Information</h4>
          <p className="mb-3">
            Corravale does not sell your information to third parties, and it does not share your
            information with third parties for any purpose other than supporting the legitimate interests
            and operations of the University.
          </p>
          <p className="mb-6">
            We rely on a range of third-party services to help carry out the University's business. We
            work hard to uphold the confidentiality, privacy, and security standards that we require of
            all our service providers, and we work to ensure that they use your personal information only
            for the purpose of providing those services.
          </p>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">How We Secure Your Information</h4>
          <p className="mb-6">
            Corravale understands how important it is to maintain the security of the information it
            collects and holds, and we work to protect that information from unauthorized access and
            harm. Corravale strives to keep reasonable security measures in place, including physical,
            administrative, and technical safeguards, to protect your personal information.
          </p>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Privacy Statement Changes</h4>
          <p className="mb-6">
            This privacy statement may be revised from time to time. We will post the date of the most
            recent update at the top of this page.
          </p>

          <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Who to Contact with Questions or Concerns</h4>
          <p className="mb-6">
            If you have any concerns or questions about how your personal data is being used, please
            contact the <Link to="/_404.html" className="text-[#1a5fa8] underline">Data Privacy Office</Link>.
          </p>

          <h4 className="mt-6 mb-3 font-cond text-[18px] text-[#00274c]">Special Notices</h4>
          <Disclosure id="coppa" label="Persons under the age of 13, or their parents or guardians">
            <p>
              COPPA places legal and regulatory obligations on certain operators of websites or online
              services that are directed to children under 13 years of age, and on certain operators of
              other websites or online services that have actual knowledge that they are collecting
              personal information online from a child under 13 years of age. The Federal Trade
              Commission, the consumer protection agency of the United States, enforces{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">COPPA</Link>, which sets out what
              operators of websites or online services that are subject to COPPA are required to do in
              order to protect the privacy and safety of children under the age of 13 online whenever
              COPPA applies. Corravale, together with the vendors with whom we work, sometimes collects
              data from children under the age of 13, or shares such information with one another. The
              collection and sharing of this information is carried out in accordance with all applicable
              law, including COPPA to the extent that it applies in the circumstances.
            </p>
          </Disclosure>
          <Disclosure id="eu" label="Persons located within the European Union">
            <p className="mb-3">
              If you happen to be located in the EU, then the way Corravale handles your personal
              information may instead be governed by{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">
                Regulation 2016/679 (the General Data Protection Regulation, or the “GDPR”)
              </Link>
              .
            </p>
            <p className="mb-4">
              Beyond the general privacy details already outlined above, we offer further guidance that
              applies specifically to the EU legal framework, set out below. Please also see our{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">GDPR resources webpage</Link> to
              learn more.
            </p>
            <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Legal basis for processing</h5>
            <p className="mb-3">
              The lawful grounds on which Corravale processes your personal information will differ
              according to the situation at hand. As a general matter, we most commonly depend on the
              following legal bases whenever we process your personal information under the GDPR:
            </p>
            <ul className="mb-4 list-disc space-y-2 pl-6">
              <li>Necessity to enter into or to perform a contract (ex: for the online applications you submit; for the details you supply when enrolling; for the payment information we handle in connection with tuition);</li>
              <li>Necessity for our legitimate interests or those of third parties (our legitimate interest in sustaining a lasting network for graduates);</li>
              <li>Consent (for the research studies you may choose to take part in; for the processing of special categories of personal data).</li>
            </ul>
            <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Your rights</h5>
            <p className="mb-3">
              Corravale is dedicated to helping you exercise the rights that EU data protection law
              grants to you promptly and without undue delay.
            </p>
            <p className="mb-3">
              Within the scope of our processing activities that fall under the GDPR, you hold the
              following rights concerning your personal information:
            </p>
            <ul className="mb-4 list-disc space-y-2 pl-6">
              <li>Access, correction and related requests – You have the right to confirm whether we are processing your personal data, together with the right to learn what personal data we hold about you. You may also request a copy of that data. In addition, and in certain circumstances, you may have the right to seek erasure, correction, restriction and portability of the personal data we keep about you.</li>
              <li>Right to object – You may object to receiving marketing communications from us by following the opt-out steps included in our marketing emails, and you may also object, on grounds relating to your particular situation, to any processing of your personal data. Where that happens, we will review your request and reply within a reasonable time, in keeping with our legal duties.</li>
              <li>Right to withdraw consent – For every processing operation that rests on your consent, you may withdraw that consent whenever you wish, and we will cease those processing operations to the extent the law permits.</li>
            </ul>
            <p className="mb-4">
              Please keep in mind that, when you exercise these rights, if we cannot be sure of your
              identity, we may need to request additional personal information from you, which will be
              used solely for the purpose of answering your request.
            </p>
            <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Retention period</h5>
            <p className="mb-4">
              We aim to hold personal data in our systems only for as long as it is needed for the
              purposes for which it was gathered and processed. Retention periods differ and are set with
              regard to our legitimate interests and every applicable legal requirement.
            </p>
            <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Data transfers</h5>
            <p className="mb-4">
              When you engage with Corravale, your personal information is transferred to the United
              States. The United States is not presently among the countries outside the European Union
              that the European Commission has recognized as offering an adequate level of legal
              protection for personal information. To make sure that transfers of personal information
              from the EU remain lawful, Corravale relies on the derogations set out in Article 49 GDPR.
              Specifically, we rely on your explicit consent for certain transfers and on necessity for
              the performance of a contract or the carrying out of pre-contractual steps taken at your
              request (for example, for the transfer of personal data required to process your
              application for admission). Even so, please be assured that we put safeguards in place for
              the information transferred, as the GDPR itself requires and in line with this General
              Privacy Statement.
            </p>
            <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Concerns</h5>
            <p>
              Should you have any concerns or questions about the ways in which your personal data is
              used, please reach out to the{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">Data Privacy Office</Link>. We
              will respond to your request without delay and do all we can to resolve your concern. If,
              however, you feel that we have not handled your concern as it should be, you have the right
              to lodge a complaint with your local data protection authority, as provided by Article 77
              of the GDPR. You are also entitled to file a complaint in the Member State of your
              residence, your place of work, or where an alleged breach of the GDPR occurred.
            </p>
          </Disclosure>
        </div>
      </section>
    </>
  );
}
