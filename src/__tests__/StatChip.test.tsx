import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { StatChip } from '../components/StatChip';

// Mock the Icon component to avoid image require issues
jest.mock('../components/Icon', () => ({
  Icon: ({ testID }: any) => {
    const { View } = require('react-native');
    return <View testID={testID || 'icon'} />;
  },
}));

// Mock the batched delta hook to make tests synchronous
jest.mock('../hooks/useBatchedDelta', () => ({
  useBatchedDelta: (commit: (d: number) => void) => {
    const React = require('react');
    const [pending, setPending] = React.useState(0);
    return {
      pending,
      bump: (delta: number) => {
        setPending((p: number) => p + delta);
        commit(delta);
      },
      flush: () => setPending(0),
    };
  },
}));

const MOCK_ICON = 1; // numeric asset ID

describe('StatChip', () => {
  it('renders without crashing', () => {
    const onChange = jest.fn();
    const { toJSON } = render(
      <StatChip testID="chip" iconSource={MOCK_ICON} value={0} color="#ff0000" onChange={onChange} />,
    );
    expect(toJSON()).toBeTruthy();
  });

  it('calls onChange(+1) on press (short tap)', () => {
    const onChange = jest.fn();
    const { getByTestId } = render(
      <StatChip testID="chip" iconSource={MOCK_ICON} value={0} color="#ff0000" onChange={onChange} />,
    );

    fireEvent.press(getByTestId('chip'));

    expect(onChange).toHaveBeenCalledWith(1);
  });

  it('calls onChange(-1) on long press', () => {
    const onChange = jest.fn();
    const { getByTestId } = render(
      <StatChip testID="chip" iconSource={MOCK_ICON} value={2} color="#ff0000" onChange={onChange} />,
    );

    fireEvent(getByTestId('chip'), 'longPress');

    expect(onChange).toHaveBeenCalledWith(-1);
  });

  it('does not show badge when value is 0', () => {
    const onChange = jest.fn();
    const { queryByText } = render(
      <StatChip testID="chip" iconSource={MOCK_ICON} value={0} color="#ff0000" onChange={onChange} />,
    );

    expect(queryByText('0')).toBeNull();
  });

  it('shows badge with value when active (value > 0)', () => {
    const onChange = jest.fn();
    const { getByText } = render(
      <StatChip testID="chip" iconSource={MOCK_ICON} value={3} color="#ff0000" onChange={onChange} />,
    );

    expect(getByText('3')).toBeTruthy();
  });

  it('multiple taps accumulate in display', () => {
    const onChange = jest.fn();
    const { getByTestId, getByText } = render(
      <StatChip testID="chip" iconSource={MOCK_ICON} value={1} color="#ff0000" onChange={onChange} />,
    );

    fireEvent.press(getByTestId('chip'));
    fireEvent.press(getByTestId('chip'));

    // value(1) + pending(2) = 3
    expect(getByText('3')).toBeTruthy();
  });
});
