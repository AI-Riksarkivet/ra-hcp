missing features currently
- start with storybook for visual testing.

bugs:
- [SOLVED] ownership shown and can be set in namespaces/<namespace> - pencil icon to edit owner inline, also added owner field to create dialog
- [SKIPPED] network settings — system-level admin only (403 for tenant users). Tenant-level SNMP/Syslog logging flags exist in backend but not yet exposed in frontend settings UI. Add later when needed.
- [SOLVED] invalid date on created in /buckets - formatDate now handles empty/invalid dates
- [SOLVED] Can we not create a template without importing? — added "Create from Scratch" option alongside file import, with inline editing, add/remove namespace entries, and per-entry trash button
- [SOLVED] button should never be flexed — removed w-full from template import Create/Start Over buttons, now right-aligned with normal sizing
- [SOLVED] Missing feature to add the exact user rights — namespace access section on /users/<user> and /users/groups/<group> is now fully editable with clickable permission badges, add/remove namespaces via dropdown, select all/clear all, and save button
- [SOLVED] replication collision import error: deleteDays now stripped when deleteEnabled is false
- [NEEDS INPUT] error in rights with full control: Access Denied on /buckets/ai-icelandic-ner — this is an HCP-side permission issue (user doesn't have WRITE_ACL on that namespace), not a frontend bug
- [SOLVED] edit (pencil) for tags in namespace table - fixed async save callback so save state is properly tracked
- [SOLVED] copy button for S3 credentials and reveal eye icon - fixed prop spread order so onclick handlers aren't overridden by tooltip props
- [SOLVED] buckets page only showed owned buckets - merged MAPI namespaces into bucket list
- [SOLVED] access control page only showed owned buckets - same fix applied to ACL table and grant dialog

