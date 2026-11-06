import AccountFlow from './auth/AccountFlow';

// This standalone app delivers account access only.
// Teammates own onboarding and all later screens; see docs/HANDOFF.md.
export default function App() {
  return <AccountFlow />;
}
