import { cn } from "../../utils/cn";

const variants = {
  primary:
    "bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 active:scale-[0.98] disabled:opacity-60 text-white font-semibold tracking-wide",
  ghost: "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
  outline: "border border-gray-200 hover:bg-gray-50 text-gray-500 font-medium",
};

const sizes = {
  sm: "py-2 px-3 text-sm",
  md: "py-2.5 px-4 text-sm",
  lg: "py-3.5 px-5 text-sm",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  leftIcon?: React.ReactNode;
}

const ButtonCustom = ({
  children,
  variant = "primary",
  size = "md",
  leftIcon,
  className,
  ...rest
}: ButtonProps) => {
  return (
    <button
      {...rest}
      className={cn(
        "w-full rounded-xl flex items-center justify-center gap-2 transition-all duration-150 cursor-pointer",
        variants[variant],
        sizes[size],
        className,
      )}
    >
      {leftIcon && leftIcon}
      {children}
    </button>
  );
};

export default ButtonCustom;
