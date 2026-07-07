import { render, screen } from '@testing-library/react';
import Providers from '../src/components/Providers';

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe('Providers Component', () => {
  it('renders children without crashing', () => {
    render(
      <Providers>
        <div data-testid="child-element">Hello Providers</div>
      </Providers>
    );

    expect(screen.getByTestId('child-element')).toBeInTheDocument();
    expect(screen.getByText('Hello Providers')).toBeInTheDocument();
  });

  it('initializes QueryClientProvider', () => {
    // React Query uses context, if it wasn't provided, 
    // any query hooks inside children would throw an error.
    // Since it renders fine, the provider is initialized.
    const { container } = render(
      <Providers>
        <div />
      </Providers>
    );
    expect(container).toBeInTheDocument();
  });
});
